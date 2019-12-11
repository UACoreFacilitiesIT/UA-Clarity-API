"""An API to that interacts with Clarity REST architecture."""
import re
import os
import tempfile
from jinja2 import Template
from bs4 import BeautifulSoup
from ua_generic_rest_api import ua_generic_rest_api
from ua_clarity_api import get_endpoint_map


class ClarityApi(ua_generic_rest_api.GenericRestApi):
    """Contains basic Clarity REST API functionality from CLI or EPP calls."""
    def __init__(self, host, username, password):
        headers = {"Content-Type": "application/xml"}
        super().__init__(host, headers, "start-index")
        self.session.auth = (username, password)

    def get(self, endpoints, parameters=None, get_all=True):
        # Collect info to find out if the endpoint(s) can be batched.
        batchable = _is_batchable(endpoints)

        if isinstance(endpoints, str):
            endpoints = [endpoints]

        # Find the resource, located after the last '/'.
        specific_endpoint = endpoints[0].split("v2/")[-1]
        specific_endpoint = specific_endpoint.split('?')[0]
        specific_endpoint = specific_endpoint.strip('/')
        resource = None
        for key in get_endpoint_map.get_pattern_resource:
            if re.search(key, specific_endpoint):
                resource = get_endpoint_map.get_pattern_resource.get(key)
        if resource is None:
            raise KeyError(
                f"The endpoint {endpoints[0]} is not gettable.")

        contents = list()
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

        else:
            # Get the .text(s) of the super's get.
            get_responses = super().get(endpoints, parameters)

            if len(get_responses) > 1:
                for response in get_responses:
                    response_soup = BeautifulSoup(response.text, "xml")
                    contents.append(response_soup)

            elif len(get_responses) == 1:
                response_soup = BeautifulSoup(get_responses[0].text, "xml")

                # Harvest all of the next-pages of an endpoint if desired.
                if response_soup.find("next-page") and get_all:
                    contents = self._harvest_all_resource(
                        endpoints[0], resource, list())

                else:
                    # If the next pages aren't desired and there's 1 endpoint.
                    return get_responses[0].text

            else:
                return get_responses

            # Return all of the contents from all pages as 1 xml.
            template_path = os.path.join(
                os.path.split(__file__)[0], "get_multiple_items.xml")
            with open(template_path, 'r') as file:
                template = Template(file.read())
                get_xml = template.render(contents=contents)

            return get_xml

    def put(self, endpoint, payload):
        """Return the .text of the put response."""
        return super().put(endpoint, payload).text

    def post(self, endpoint, payload):
        """Return the .text of the post response."""
        return super().post(endpoint, payload).text

    def download_files(self, uris, file_key=True):
        """Retrieves files from Clarity server, returns as uri:tempfile dict.

        Arguments:
            file_uris (list):
                The list of desired file_uri's (or artifact uri's that contain
                    a 'file:file' tag, with a limsid that starts with '92-').
            file_key (boolean):
                If True, the key will be a file uri. If False, the key will be
                    an artifact uri.

        Returns:
            uris_files (dict):
                file_uris or art_uris: unencoded tempfile.
        """
        # Harvest the file uri from the art uri, and map the two if file_key is
        # False.
        art_uris = set()
        for uri in uris:
            if "artifacts/" in uri or uri.split('/')[-1].startswith("92-"):
                art_uris.add(uri)

        if art_uris:
            file_art_uris = dict()
            arts_soup = BeautifulSoup(self.get(list(art_uris)), "xml")
            for soup in arts_soup.find_all("art:artifact"):
                # If an artifact has not yet been given a file uri, continue.
                if soup.find("file:file"):
                    file_art_uris[soup.find("file:file")["uri"]] = soup[
                        "uri"].split('?')[0]

            file_uris = file_art_uris.keys()
        else:
            file_uris = uris

        file_uri_check = ["file" in uri for uri in file_uris]
        # Assert uris are batchable, there's only 1 resource, and the uri's
        #  are file uri's.
        if not _is_batchable(file_uris) or False in file_uri_check:
            raise ValueError("The argument passed in were not file uri's.")

        # Create a dict of file_uris to their file contents.
        uris_file_content = dict()
        for file_uri in file_uris:
            response = self.session.get(f"{file_uri}/download", timeout=10)
            response.raise_for_status()

            if file_key:
                uris_file_content[file_uri] = response.content
            else:
                uris_file_content[file_art_uris[file_uri]] = response.content

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
            response = self.session.get(next_page_uri, timeout=60)
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
