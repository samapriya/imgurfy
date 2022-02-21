import argparse
import getpass
import json
import os
import webbrowser
from os.path import expanduser

import requests
from logzero import logger

BASE_URL = "https://api.imgur.com"


def iminit():
    uname = str(input("Enter your username: "))
    cid = str(input("Enter your Client ID:  "))
    cpass = getpass.getpass("Enter your Client Secret:  ")
    while len(cpass) == 0:
        logger.warning("Client Secret is empty: try again")
        cpass = getpass.getpass("Enter your Client Secret:  ")
    try:
        browse_link = webbrowser.open(
            f"https://api.imgur.com/oauth2/authorize?client_id={cid}&response_type=token",
            new=2,
        )
        if browse_link is False:
            print("Your setup does not have a monitor to display the webpage")
            print(
                f"Go to https://api.imgur.com/oauth2/authorize?client_id={cid}&response_type=token"
            )
    except Exception as error:
        print(error)
    cauth = str(input("Enter your authenticated url from address bar:  "))
    token = cauth.split("access_token=")[1].split("&")[0]
    refresh = cauth.split("refresh_token=")[1].split("&")[0]
    token_data = {
        "username": uname,
        "cs": cpass,
        "cid": cid,
        "token": token,
        "refresh_token": refresh,
    }
    with open(os.path.join(expanduser("~"), "imcred.json"), "w") as outfile:
        json.dump(token_data, outfile, indent=2)
    logger.info("Auth profile setup complete")


def iminit_from_parser(args):
    iminit()


# iminit()


def imgur_auth():
    if os.path.exists(os.path.join(expanduser("~"), "imcred.json")):
        with open(os.path.join(expanduser("~"), "imcred.json"), "r") as f:
            data = json.load(f)
    else:
        iminit()
        imgur_auth()
    url = f"{BASE_URL}/oauth2/token"
    payload = {
        "refresh_token": data["refresh_token"],
        "client_id": data["cid"],
        "client_secret": data["cs"],
        "grant_type": "refresh_token",
    }

    response = requests.request("POST", url, data=payload)
    cred_json = response.json()
    cred_json["cid"] = data["cid"]

    return [data["username"], cred_json]


def info():
    username, cred_json = imgur_auth()
    url = f"{BASE_URL}/3/account/{username}"
    payload = {}
    files = {}
    headers = {"Authorization": f"Bearer {cred_json['access_token']}"}
    response = requests.get(url, headers=headers, data=payload, files=files)
    if response.status_code == 200:
        print(json.dumps(response.json()["data"], indent=2))


def info_from_parser(args):
    info()


def imgur_album_create(title, description):
    url = f"{BASE_URL}/3/album"
    folder_lists = os.path.join(expanduser("~"), "imgur_folders.json")
    username, cred_json = imgur_auth()
    headers = {"Authorization": f"Bearer {cred_json['access_token']}"}
    payload = {
        "title": title,
        "description": description,
    }
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        album_id = response.json()["data"]["id"]
        album_hash = response.json()["data"]["deletehash"]
        print(f"Created album name {title} : with ID {album_id} and hash {album_hash}")
        if os.path.exists(folder_lists):
            with open(folder_lists, "r") as f:
                data = json.load(f)
                data.append({album_id: album_hash})
            with open(folder_lists, "w") as outfile:
                json.dump(data, outfile, indent=2, sort_keys=True)
        else:
            folder_info = [{album_id: album_hash}]
            with open(folder_lists, "w") as outfile:
                json.dump(folder_info, outfile, indent=2, sort_keys=True)
    else:
        print(f"Failed to create album with response code {response.status_code}")


def mkalbum_from_parser(args):
    imgur_album_create(
        title=args.title,
        description=args.description,
    )


def imgur_albumlist():
    username, cred_json = imgur_auth()
    api_host = f"{BASE_URL}/3/account/{username}/albums/"
    payload = {}
    files = {}
    headers = {"Authorization": f"Bearer {cred_json['access_token']}"}

    response = requests.get(api_host, headers=headers, data=payload, files=files)
    if response.status_code == 200:
        resp = response.json()
        album_list = []
        for album in resp["data"]:
            album_info = {}
            album_info["title"] = album["title"]
            album_info["id"] = album["id"]
            album_info["images_count"] = album["images_count"]
            album_info["deletehash"] = album["deletehash"]
            album_list.append(album_info)
        print(json.dumps(album_list, indent=2))


def album_info(aid):
    print("")
    folder_lists = os.path.join(expanduser("~"), "imgur_folders.json")
    username, cred_json = imgur_auth()
    headers = {"Authorization": f"Bearer {cred_json['access_token']}"}
    if aid is None:
        imgur_albumlist()
    elif aid is not None:
        url = f"{BASE_URL}/3/album/{aid}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            resp = response.json()
            album = resp["data"]
            album_info = {}
            album_info["title"] = album["title"]
            album_info["id"] = album["id"]
            album_info["images_count"] = album["images_count"]
            album_info["deletehash"] = album["deletehash"]
            print(json.dumps(album_info, indent=2))


def ialbum_from_parser(args):
    album_info(aid=args.aid)


def albumlist_from_parser(args):
    imgur_albumlist(username=args.username)


def imgur_uploader(**kwargs):
    api_host = f"{BASE_URL}/3/image"
    username, cred_json = imgur_auth()
    headers = {"Authorization": f"Bearer {cred_json['access_token']}"}
    config = {}
    for key, value in kwargs.items():
        if key == "path" and value is not None:
            img_path = value
        if key == "name" and value is not None:
            config["name"] = value
        if key == "title" and value is not None:
            config["title"] = value
        if key == "album" and value is not None:
            config["album"] = value
        if key == "description" and value is not None:
            config["description"] = value
    with open(img_path, "rb") as img:
        files = {"image": img}
        response = requests.post(api_host, files=files, headers=headers, data=config)
        if response.status_code == 200:
            print(
                "\n"
                + f"{os.path.basename(img_path)} : {response.json()['data']['link']}"
            )
            return {"success": True, "data": response.json()["data"]["link"]}
        else:
            print(response.status_code)
            return {"success": False}


def upload_from_parser(args):
    imgur_uploader(
        path=args.path,
        name=args.name,
        title=args.title,
        description=args.description,
        album=args.album,
    )


def main(args=None):
    parser = argparse.ArgumentParser(description="Simple CLI for Imgur API")
    subparsers = parser.add_subparsers()

    parser_iminit = subparsers.add_parser(
        "init", help="Initialize Imgur application & setup client credentials"
    )
    parser_iminit.set_defaults(func=iminit_from_parser)

    parser_info = subparsers.add_parser(
        "info",
        help="Summarizes your user info based on your initialized username & credentials",
    )
    parser_info.set_defaults(func=info_from_parser)

    parser_upload = subparsers.add_parser("upload", help="Upload media to Imgur")
    required_named = parser_upload.add_argument_group("Required named arguments.")
    required_named.add_argument("--path", help="Full path to media", required=True)
    optional_named = parser_upload.add_argument_group("Optional named arguments")
    optional_named.add_argument("--name", help="image name", default=None)
    optional_named.add_argument("--title", help="image title", default=None)
    optional_named.add_argument("--description", help="image description", default=None)
    optional_named.add_argument("--album", help="album hex id", default=None)
    parser_upload.set_defaults(func=upload_from_parser)

    parser_mkalbum = subparsers.add_parser("mkalbum", help="Create Imgur album")
    required_named = parser_mkalbum.add_argument_group("Required named arguments.")
    required_named.add_argument("--title", help="album title", required=True)
    optional_named = parser_mkalbum.add_argument_group("Optional named arguments")
    optional_named.add_argument("--description", help="album description", default=None)
    parser_mkalbum.set_defaults(func=mkalbum_from_parser)

    parser_ialbum = subparsers.add_parser(
        "ialbum", help="Album Info or info on all saved albums"
    )
    optional_named = parser_ialbum.add_argument_group("Optional named arguments")
    optional_named.add_argument("--aid", help="album id", default=None)
    parser_ialbum.set_defaults(func=ialbum_from_parser)

    args = parser.parse_args()

    try:
        func = args.func
    except AttributeError:
        parser.error("too few arguments")
    func(args)


if __name__ == "__main__":
    main()
