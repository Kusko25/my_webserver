from typing import Any

from bs4 import BeautifulSoup
import requests

class Gallery:
    def __init__(self, url:str) -> None:
        self.url = url
        response = requests.get(url=url)
        if response.status_code == 200:
            self.gallery_html = response.text
        else:
            self.gallery_html = ""
    
    tags_ = None
    @property
    def tags(self):
        if self.tags_ is not None:
            return self.tags_
        
        prefix_whitelist = {"language","female","male","other","artist"}
        soup = BeautifulSoup(self.gallery_html,"html.parser")
        tags = []
        tag_table = soup.select_one("#taglist table")
        assert tag_table is not None
        for row in tag_table.find_all("tr"):
            row_prefix = row.select_one("td.tc")
            assert row_prefix is not None
            row_prefix = row_prefix.text
            
            print(row_prefix)
            if row_prefix[:-1] not in prefix_whitelist:
                continue
            for tag in row.select("div a"):
                tags.append(row_prefix + tag.text)
        self.tags_ = tags
        return tags

class GraphQL:
    endpoint = "http://localhost:9999/graphql"
    
    def headers(self):
        headers_dict = {
            "Content-Type": "application/json"
        }
        return headers_dict
    
    def query(self,query):
        response = requests.post(
            url=self.endpoint,
            json={"query": query},
            headers=self.headers()
        )
        return response
    
    def tag_id(self,tag_name):
        query = """{
            findTags(tag_filter: {
                name: {
                value: "%s"
                modifier: EQUALS
                }
            }) {
                tags {
                name
                id
                }
            }
        }
        """ % tag_name
        response = self.query(query=query)
        response_data = response.json()
        if len(response_data["data"]["findTags"]["tags"])>0:
            return response_data["data"]["findTags"]["tags"][0]["id"]
        else:
            return None
    
    def tag_make(self, input:dict[str,Any]):
        body = """mutation {
        tagCreate(input: {
            %s
        }) {
            id
        }
        }""" % "\n".join(f'{key}: "{value}"' for key,value in input.items())
        response = self.query(query=body)
        if response.status_code == 200:
            return True
        else:
            print(response.json())
            return False
    
    def tag_exists(self,tag_name):
        if self.tag_id(tag_name) is not None:
            return True
        return False