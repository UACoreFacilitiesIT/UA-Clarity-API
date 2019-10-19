"""An API to that interacts with Clarity REST architecture."""
import re
import os
import tempfile
import urllib
import concurrent.futures
import asyncio
import requests
from bs4 import BeautifulSoup
from jinja2 import Template
from ua_clarity_api import get_endpoint_map


class ClarityApi:
    """Contains basic Clarity REST API functionality from CLI or EPP calls."""
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password

    def get(self, endpoints, parameters=None, get_all=True):
        """Get the xml of the endpoint or endpoints passed in.

        Arguments:
            endpoints (string or list):
                The REST resource(s) you want to get. Can be a single endpoint
                or a list of them. endpoint's can be both the full endpoint, or
                just the endpoint after v2/.
            parameters (dict):
                A mapping of a query-able name: value. NOTE: queries can only
                be added to a single endpoint.
            get_all (bool):
                If there are next-page tags on that resource, whether get
                should return all of the resources on all pages or just the
                first page.

        Returns:
            (string):
                The aggregate xml for the get, including all provided
                endpoint's and queries as a well-formed xml string.
        """
        # If the endpoints is a str of one endpoint, turn it into a list.
        if isinstance(endpoints, str):
            endpoints = [endpoints]

        # Add the base url if it was not included on any requested endpoint.
        for i, endpoint in enumerate(endpoints):
            if self.host not in endpoint:
                endpoints[i] = f"{self.host}{endpoint}"

        # Find the resource, located after the last '/'.
        specific_endpoint = endpoints[0].split("v2/")[-1]
        specific_endpoint = specific_endpoint.strip('/')
        resource = None
        for key in get_endpoint_map.get_pattern_resource:
            if re.search(key, specific_endpoint):
                resource = get_endpoint_map.get_pattern_resource.get(key)
        if resource is None:
            raise KeyError(f"The endpoint {endpoints[0]} is not gettable.")

        # Build endpoint with query if a parameters dict is given.
        if parameters:
            query = _query_builder(parameters)
            endpoints[0] += query

        batchable = _is_batchable(endpoints)

        template_path = os.path.join(
            os.path.split(__file__)[0], "get_multiple_items.xml")

        # Batch get.
        if batchable:
            template_path = os.path.join(
                os.path.split(__file__)[0], "post_batch_receive_template.xml")

            with open(template_path, 'r') as file:
                template = Template(file.read())
                post_xml = template.render(
                    urls=endpoints, resource=resource)

            batch_endpoint = (
                f"{self.host}{specific_endpoint.split('/')[0]}/batch/retrieve")

            return self.post(batch_endpoint, post_xml)

        # Brute batch get.
        elif len(endpoints) > 1:
            responses = self._brute_batch_get(endpoints)
            contents = list()
            for response in responses:
                response_soup = BeautifulSoup(response.text, "xml")
                contents.append(response_soup.find(resource))

        # Single get.
        else:
            if get_all:
                contents = self._harvest_all_resource(
                    endpoints[0], resource, list())

            else:
                response = requests.get(
                    endpoints[0],
                    auth=(self.username, self.password),
                    timeout=10)
                response.raise_for_status()
                return response.text

        with open(template_path, 'r') as file:
            template = Template(file.read())
            get_xml = template.render(contents=contents)

        return get_xml

    def put(self, endpoint, payload):
        """Put the xml passed in.

        Arguments:
            endpoint (string):
                The REST endpoint to which you want to put.
            payload (string):
                The xml to put to the specific endpoint.

        Returns:
            (string):
                The returned endpoint information as an xml-parsable string.
        """
        if self.host in endpoint:
            full_url = endpoint
        else:
            full_url = f"{self.host}{endpoint}"

        headers = {"Content-type": "application/xml"}
        response = requests.put(
            full_url,
            str(payload),
            auth=(self.username, self.password),
            headers=headers)
        response.raise_for_status()

        return response.text

    def post(self, endpoint, payload):
        """Post the xml passed in.

        Arguments:
            endpoint (string):
                The REST endpoint to which you want to post.
            payload (string):
                The xml to post to the specific endpoint.

        Returns:
            (string):
                The returned endpoint information as an xml-parsable string.
        """
        if self.host in endpoint:
            full_url = endpoint
        else:
            full_url = f"{self.host}{endpoint}"

        headers = {"Content-type": "application/xml"}
        response = requests.post(
            full_url,
            str(payload),
            auth=(self.username, self.password),
            headers=headers)
        response.raise_for_status()

        return response.text

    def delete(self, full_url):
        """Delete the uri within Clarity, returning the delete response."""
        headers = {"Content-type": "application/xml"}
        response = requests.delete(
            full_url,
            auth=(self.username, self.password),
            headers=headers)
        response.raise_for_status()

        return response

    def download_files(self, file_uris):
        """Retrieves files from Clarity server, returns as uri:tempfile dict.

        Arguments:
            file_uris (list):
                The list of desired file_uri's.

        Returns:
            uris_files (dict):
                file_uris: unencoded tempfile.
        """
        file_uri_check = ["file" in uri for uri in file_uris]
        # Assert uris are batchable, there's only 1 resource, and the uri's
        #  are file uri's.
        if not _is_batchable(file_uris) or False in file_uri_check:
            raise ValueError("The argument passed in were not file uri's.")

        # Create a dict of file_uris to their file contents.
        uris_file_content = dict()
        for uri in file_uris:
            response = requests.get(
                f"{uri}/download",
                auth=(self.username, self.password),
                timeout=10)
            response.raise_for_status()
            uris_file_content[uri] = response.content

        # For each file uri, create a tempfile, write their contents into it,
        # and map the tempfile to the uri.
        uris_files = dict()
        for uri in uris_file_content:
            uris_files[uri] = tempfile.NamedTemporaryFile()
            uris_files[uri].write(uris_file_content[uri])
            uris_files[uri].seek(0)

        return uris_files

    def _harvest_all_resource(self, next_page_uri, resource, contents):
        """Recursively harvests all resources from next-page'd get requests."""
        if next_page_uri:
            response = requests.get(
                next_page_uri,
                auth=(self.username, self.password),
                timeout=10)
            response.raise_for_status()

            response_soup = BeautifulSoup(response.text, "xml")
            contents.extend(response_soup.find_all(resource))
            next_page_tag = response_soup.find("next-page")

            if next_page_tag:
                next_page_uri = next_page_tag["uri"]
            else:
                next_page_uri = None

            return self._harvest_all_resource(
                next_page_uri, resource, contents)

        else:
            return contents

    def _brute_batch_get(self, urls):
        """Uses threading to GET a list of urls and returns the responses.

        Arguments:
            uris (list):
                A list of complete urls.

        Return:
            responses (list):
                List of requests response objects.
        """
        # Setup event loop for async calls.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Execute calls and get responses.
        responses = loop.run_until_complete(self._get_async(urls))

        return responses

    async def _get_async(self, urls):
        """Uses ThreadPoolExecutor to GET the list of uris.

        Arguments:
            uris (list):
                A list of completed uris to make using requests.
        Return:
            A list containing the HTTP responses as dictionaries.
        """
        def single_get(url):
            response = requests.get(
                url, auth=(self.username, self.password), timeout=10)
            response.raise_for_status()
            return response

        # Set up executor.
        with concurrent.futures.ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()

            # Store futures to gather.
            futures = list()
            for url in urls:
                futures.append(loop.run_in_executor(
                    executor,
                    single_get,
                    url
                ))

            # Return data when completed.
            return await asyncio.gather(*futures)


def _is_batchable(urls):
    """Verifies list of uri's is batchable, returning a boolean."""
    resources = set()
    search_string = (
        r"v2/(artifacts|containers|files|samples|)/[A-Za-z0-9-]+")
    for url in urls:
        found = None
        found = re.search(search_string, url)
        if found:
            if "download" not in url and "upload" not in url:
                resources.add(found.group(0).split("/")[1])

    resources = list(resources)

    if len(resources) > 1:
        raise ValueError(
            f"You have passed in 2 or more types of uri's in: {urls}."
            f" this method requires that your uri's all post to the"
            f" same endpoint. The following resources were found: {resources}")
    if len(resources) == 1:
        return True

    return False


def _query_builder(parameters):
    """Converts dictionary with queries to http-able query."""
    single_parameters = dict()
    multi_parameters = dict()
    for key in parameters:
        if isinstance(parameters[key], list):
            multi_parameters.setdefault(key, parameters[key])
        else:
            single_parameters[key] = parameters[key]

    final_query = urllib.parse.urlencode(single_parameters)

    for key, group in multi_parameters.items():
        for parameter in group:
            final_query += f"&{key}={parameter}"

    return f"?{final_query}"
