import argparse
import base64
from graphql import parse
from graphql import Source
from graphql import print_ast
import json
import os
from urllib.parse import urlparse
import xml.etree.ElementTree as ET


def error(msg):
    """
    Log an error message
    """
    print("[-] {msg}".format(msg=msg))

def log(msg):
    """
    Log a success message
    """
    print("[+] {msg}".format(msg=msg))

def write_to_file(filepath, contents):
    """
    Writes the specified contents to a file
    specified by filepath
    """
    with open(filepath, "wb") as f:
        f.write(contents)

def tokenize_graphql_variables():
    """
    Parses a GraphQL query and replaces
    variable values with tokens to be used
    for targeted injections
    """
    pass

def tokenize_graphql_parameters(query):
    """
    Parses a GraphQL query and replaces
    parameter values with tokens to be used
    for targeted injections
    """
    document = parse(query)
    for arg in document.definitions[0].selection_set.selections[0].arguments:
        arg.value.value = "*"
    return print_ast(document)

def detect_graphql(payload):
    """
    """
    return "query" in payload

def handle_graphql_json(payload):
    """
    Convert payload body (i.e. GraphQL query)
    to JSON for easier handling
    """
    payload_json = json.loads(payload)
    
    if detect_graphql(payload_json):
        log("Appears to be a valid GraphQL query...")
        result = tokenize_graphql_parameters(payload_json["query"])
        payload_json["query"] = result
        return payload_json
    else:
        error("HTTP payload body is not a valid GraphQL query")
    return None

def replace_http_req_body(contents, new_payload):
    return b"%b\n%b" % (b"\n".join(contents.split(b"\n")[:-1]), new_payload)

def extract_http_req_body(contents):
    """
    Splits the HTTP request by new lines and gets the
    last line which is the HTTP payload body
    """
    return contents.split(b"\n")[-1]

def process_xml_file(xmlroot):
    """
    Process the element of the XML file
    """
    counter = 0
    for child in xmlroot:
        parsed_url = urlparse(child.find("url").text).path
        if parsed_url.startswith("/"):
            parsed_url = parsed_url[1:]
        dest = "{}-{}.txt".format(parsed_url, counter)
        contents = base64.b64decode(child.find("request").text)

        body = extract_http_req_body(contents)
        modified_query = handle_graphql_json(body)

        body = replace_http_req_body(contents, json.dumps(modified_query).encode("utf-8"))
        print(body)
        print("Writing response to {path}".format(path=dest))
        write_to_file(dest, body)
        counter += 1

def parse_xml_file(infile):
    """
    Parse an XML file
    """
    tree = ET.parse(infile)
    print(dir(tree))
    process_xml_file(tree.getroot())

def deterine_file_type(infile):
    """
    Determine file type and route to the
    correct processor
    """
    _, file_extension = os.path.split(infile)
    if "xml" in file_extension:
        log("Parsing XML input file...")
        parse_xml_file(infile)
    else:
        error("Unsupported file type.")

def parse_file(infile):
    """
    Starts parsing a file by checking first to see if it is valid
    """
    if not os.path.exists(infile):
        error("{file} does not exist. Please verify the path and try again.".format(file=infile))
    else:
        deterine_file_type(infile)

def parse_args():
    """
    Parses the program arguments
    """
    parser = argparse.ArgumentParser("Parses HTTP GraphQL requests and identifies parameters for injection")
    parser.add_argument("--infile", dest="infile", required=True, help="The XML inputfile containing HTTP requests recorded by Burp Proxy")
    return parser.parse_args()

if __name__ == "__main__":
    """
    Main application entry point
    """
    args = parse_args()
    parse_file(args.infile)
    
