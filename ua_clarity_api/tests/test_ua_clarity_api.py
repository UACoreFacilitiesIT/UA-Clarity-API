import tempfile
import json
from unittest import TestCase
from datetime import datetime
import requests
from nose.tools import raises
from jinja2 import Template
from bs4 import BeautifulSoup
from ua_clarity_api import ua_clarity_api


class TestUAClarityApi(TestCase):
    def setUp(self):
        with open("dev_lims_creds.json", "r") as file:
            creds = json.loads(file.read())
        self.api = ua_clarity_api.ClarityApi(
            creds["host"], creds["username"], creds["password"])

    def test_get_batch_resource_single_container(self):
        post_con_uri = self._post_container()

        get_batch_response = self.api.get([post_con_uri])
        get_batch_soup = BeautifulSoup(get_batch_response, "xml")
        get_batch_uri = get_batch_soup.find("con:container")["uri"]

        assert post_con_uri == get_batch_uri

    def test_get_multiple_uris_faster_with_multithread(self):
        get_response = requests.get(
            f"{self.api.host}configuration/udfs",
            auth=(self.api.username, self.api.password),
            timeout=10)
        get_response_soup = BeautifulSoup(get_response.text, "xml")
        conf_uris = [
            soup["uri"] for soup in get_response_soup.find_all("udfconfig")]
        conf_uris = conf_uris[:20]
        single_thread_time = datetime.now()
        for uri in conf_uris:
            requests.get(
                f"{self.api.host}configuration/udfs",
                auth=(self.api.username, self.api.password),
                timeout=10)
        single_thread_time = datetime.now() - single_thread_time

        multi_thread_time = datetime.now()
        self.api.get(conf_uris)
        multi_thread_time = datetime.now() - multi_thread_time

        assert single_thread_time > multi_thread_time

    def test_get_multiple_uris_larger_than_thread_pool(self):
        get_response = requests.get(
            f"{self.api.host}configuration/udfs",
            auth=(self.api.username, self.api.password),
            timeout=10)
        get_response_soup = BeautifulSoup(get_response.text, "xml")
        conf_uris = [
            soup["uri"] for soup in get_response_soup.find_all("udfconfig")]
        get_response = self.api.get(conf_uris, get_all=False)
        get_response_soup = BeautifulSoup(get_response, "xml")
        response_uris = [
            soup["uri"] for soup in get_response_soup.find_all("cnf:field")]
        # Just in case there are < 500 udfconf.
        assert len(response_uris) > 99

        conf_uris = conf_uris[:100]
        response_uris = response_uris[:100]
        assert sorted(response_uris) == sorted(conf_uris)

    def test_get_single_uri_protocol(self):
        conf_protocol_uri = f"{self.api.host}configuration/protocols"
        response = self.api.get(conf_protocol_uri)
        response_soup = BeautifulSoup(response, "xml")
        protocol_uri = response_soup.find_all("protocol")[0]["uri"]

        protocol_response = self.api.get(protocol_uri)
        response_soup = BeautifulSoup(protocol_response, "xml")
        assert response_soup.find("step")["uri"] is not None

    def test_get_with_query(self):
        con_url = f"{self.api.host}containers"
        cons_soup = BeautifulSoup(
            self.api.get(con_url, parameters={"type": "Tube"}), "xml")
        assert [soup["uri"] for soup in cons_soup.find_all("container")]
        assert [
            soup.find("name").text for soup in cons_soup.find_all("container")]

    @raises(KeyError)
    def test_get_http_wrong_url(self):
        self.api.get("test")

    def test_put_normal_case(self):
        post_con_uri = self._post_container()

        get_response = requests.get(
            post_con_uri,
            auth=(self.api.username, self.api.password),
            timeout=10)
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
