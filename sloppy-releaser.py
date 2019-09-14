import os
import platform
import json
import requests
from pprint import pprint
from colorama import init as colorama_init
from colorama import Fore
colorama_init()


class GitLabRelease():
    def __init__(self, token, options='sloppy-releaser.json', gitlab_api_base='https://gitlab.com/api/v4', standalone=False):  # noqa: E501
        required_fields = ['id', 'tag_name', 'file', 'description']
        self.token = token
        self.gl_api = gitlab_api_base
        self.standalone = standalone

        with open(options, "r") as read_file:
            self.options = json.load(read_file)

        for field in required_fields:
            if field not in self.options:
                raise ValueError(f"Missing required field: {field}")

        if not os.access(self.options["file"], os.R_OK):
            raise ValueError(f"Release files are not readable.")

        if "description_file" in self.options:
            with open(self.options["description_file"]) as desc_file:
                self.description_file = desc_file.read()

    def upload(self):
        headers = {
            'PRIVATE-TOKEN': self.token,
        }

        uri = '{}/projects/{}/uploads'.format(self.gl_api, self.options["id"])  # noqa: E501
        # uri = 'https://httpbin.org/post'
        print(uri)
        files = {
            'file': open(self.options["file"], 'rb')
        }
        print(files)

        r_upload = requests.post(uri, headers=headers, files=files)
        if(r_upload.status_code != 201 and r_upload.status_code != 200):
            raise ValueError(f"Upload API responded with unvalid status {r_upload.status_code}")  # noqa: E501

        upload = r_upload.json()

        self.echo(f"Uploaded. Link: {self.gl_api}{upload['url']}", obj=upload)

        return upload

    def release(self, upload):
        uri = "{}/projects/{}/repository/tags/{}/release".format(self.gl_api, self.options["id"], self.options["tag_name"])
        desc = ""
        if self.options["description"] != "":
            desc = "\n#### Release Description \n\n"
            desc += self.options["description"]

        if getattr(self, "description_file", False):
            desc = self.description_file + desc

        desc += """

#### Download Exe: """ + upload["markdown"]

        headers = {
            'PRIVATE-TOKEN': self.token,
        }

        data = {
            "description": desc
        }

        r_new_release = requests.post(uri, data=data, headers=headers)
        if(r_new_release.status_code != 201 and r_new_release.status_code != 200):
            raise ValueError(f"Releases API responded with unvalid status {r_new_release.status_code}")

        self.echo("Release is complete.", obj=r_new_release.json())

    def delete_release(self):
        uri = "{}/projects/{}/releases/{}".format(self.gl_api, self.options["id"], self.options["tag_name"])
        headers = {
            'PRIVATE-TOKEN': self.token,
        }

        r_del_release = requests.delete(uri, headers=headers)
        if(r_del_release.status_code != 201 and r_del_release.status_code != 200):
            raise ValueError(f"Delete API responded with unvalid status {r_del_release.status_code}")

        self.echo("Deleted. ", obj=r_del_release.json())

    def echo(self, str, obj=None, err=False):
        if not self.standalone:
            return

        os.system("cls" if platform.system().lower() == "windows" else "clear")

        if err:
            print(Fore.RED)
            print("--- ERROR ---")

        print(str)

        if obj:
            pprint(obj)


def standalone_routine(options="sloppy-releaser.json"):
    print(Fore.GREEN)
    print("GITLAB SLOPPY RELEASER")
    print(Fore.RESET)
    mode = input("""
-- MODES --
1. Upload &  Release
2. Upload
3. Delete

J. Override default json file
Select Mode: """)

    if mode.upper() == "J":
        n_opt = input("Options json file: ")
        print("Set.")

        standalone_routine(options=n_opt)
        return

    token = input("Enter GitLab Private Token: ")
    GLR = GitLabRelease(token, options=options, standalone=True)
    try:
        if mode == "1":
            up = GLR.upload()
            GLR.release(up)
        elif mode == "2":
            up = GLR.upload()
        elif mode == "3":
            GLR.delete_release()
    except ValueError as exc:
        GLR.echo(exc)


if __name__ == "__main__":
    standalone_routine()
