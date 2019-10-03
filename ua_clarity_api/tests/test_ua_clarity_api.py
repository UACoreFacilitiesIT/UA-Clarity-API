import tempfile
import json
from unittest import TestCase
import requests
from nose.tools import raises
from jinja2 import Template
from bs4 import BeautifulSoup
from uagc_tools.gls import clarity_api


class TestUAClarityApi(TestCase):
    def setUp(self):
        with open("dev_lims_creds.json", "r") as file:
            creds = json.loads(file.read())
        self.api = clarity_api.ClarityApi(
            creds["host"], creds["username"], creds["password"])

    def test_get_normal_case(self):
        con_uri = self._post_container()

        get_response = self.api.get(con_uri)
        get_response_soup = BeautifulSoup(get_response, "xml")
        assert get_response_soup.find("con:container")["uri"] == con_uri

    @raises(KeyError)
    def test_get_http_wrong_url(self):
        self.api.get("test")

    def test_put_normal_case(self):
        post_con_uri = self._post_container()

        get_response = requests.get(
            post_con_uri, auth=(self.api.username, self.api.password))
        get_soup = BeautifulSoup(get_response.text, "xml")

        get_soup.find(
            "con:container").find("name").string = "put_test"

        put_response = self.api.put(post_con_uri, get_soup)
        put_response_soup = BeautifulSoup(put_response, "xml")
        put_con_name = put_response_soup.find(
            "con:container").find("name").text
        put_con_uri = put_response_soup.find("con:container")["uri"]

        assert put_con_name == "put_test"
        assert post_con_uri == put_con_uri

    @raises(requests.exceptions.HTTPError)
    def test_put_http_error_wrong_url(self):
        payload = self._get_container_payload()
        self.api.put("test", payload)

    def test_post_normal_case(self):
        payload = self._get_container_payload()
        response = self.api.post("containers/batch/create", payload)
        response_soup = BeautifulSoup(response, "xml")
        assert response_soup.find("link") is not None

    @raises(requests.exceptions.HTTPError)
    def test_post_http_wrong_url(self):
        payload = self._get_container_payload()
        self.api.post("test", payload)

    def test_get_batch_resource_normal_case(self):
        post_con_uri = self._post_container()

        get_batch_response = self.api.get([post_con_uri])
        get_batch_soup = BeautifulSoup(get_batch_response, "xml")
        get_batch_uri = get_batch_soup.find("con:container")["uri"]

        assert post_con_uri == get_batch_uri

    def test_delete_normal_case(self):
        con_uri = self._post_container()
        assert self.api.delete(con_uri).status_code == 204

    @raises(requests.exceptions.HTTPError)
    def test_delete_not_real_uri(self):
        self.api.delete("http://uagc-dev.claritylims.com/not-a-uri")

    def test_download_files(self):
        files_list_response = self.api.get(f"{self.api.host}files/")
        files_list_soup = BeautifulSoup(files_list_response, "xml")
        file_uris = [tag["uri"] for tag in files_list_soup.find_all("file")]

        if file_uris:
            file_uris = file_uris[:3]
            results = self.api.download_files(file_uris)

            assert sorted(list(results.keys())) == sorted(file_uris)
            for value in results.values():
                assert isinstance(value, tempfile._TemporaryFileWrapper)

        else:
            raise RuntimeError(
                "There are no files in the Clarity Dev environment. Please"
                " manually attach a file in Clarity and then attempt this test"
                " again.")

    @raises(ValueError)
    def test_get_batch_resource_two_types_uris(self):
        self.api.get([
            f"{self.api.host}containers/27-1",
            f"{self.api.host}samples/27-1"])

    def _get_container_payload(self):
        """Return a test container payload."""
        with open("post_container_template.xml") as file:
            template = Template(file.read())
            payload = template.render(
                con_name="Clarity API Container Post Test")

        return payload

    def _post_container(self):
        """Create a container and return its URI in Clarity."""
        payload = self._get_container_payload()

        headers = {"Content-type": "application/xml"}
        response = requests.post(
            f"{self.api.host}containers/batch/create",
            payload,
            auth=(self.api.username, self.api.password),
            headers=headers)

        response.raise_for_status()
        assert response.status_code == 200

        post_response_soup = BeautifulSoup(response.text, "xml")
        con_uri = post_response_soup.find("link")["uri"]

        return con_uri
