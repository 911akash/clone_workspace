#!/usr/bin/python3

import os, subprocess, argparse, sys, json


def list_folders(path):
    dirs = []
    for (root, dir, _) in os.walk(path, topdown=True):
        dirs.append(root)
    return dirs


def run_cmd(path, cmd = 'git remote get-url origin'.split()):
    os.chdir(path)
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
        raise
    return result

def write_json_file(path, dict, metadata_file_name):
    with open(os.path.join(path, metadata_file_name), 'w+') as fobj:
        json.dump(dict,fobj, indent=4)

def generatefile(path):
    dirs_covered=[]
    metadata_dict = {}
    for dir in list_folders(path):
        if any(dir_covered in dir for dir_covered in dirs_covered) or '.git' in dir:
            continue
        else:
            result = run_cmd(dir)
            if result.stdout:
                metadata_dict[dir.replace(path.rstrip('/')+'/','')] = result.stdout.decode('utf-8').strip('\n')
                dirs_covered.append(dir)

    return metadata_dict

def create_workspace(dict, workspace):
    auth_reqd = False
    for key in dict:
        new_key = os.path.join(workspace.rstrip('/'),'/'.join(key.split('/')[0:-1]))
        print(new_key)

        create_dir = 'mkdir -p {}'.format(new_key)
        print('creeate_dir: {}'.format(new_key))

        if 'ssh' in dict[key].split(':')[0]:
            git_clone = 'git clone {}'.format(dict[key])
        else:
            url_list = dict[key].split(':')
            username = os.environ.get('GIT_USERNAME')
            password = os.environ.get('GIT_PASSWORD')
            
            if username is None or password is None:
                if auth_reqd:
                    print('no username or password set : set them as env variables GIT_USERNAME and GIT_PASSWORD')
                    sys.exit()

            url_list[1] = url_list[1].replace(f'github.com',f'{username}:{password}@github.com')
            newer_url = ':'.join(url_list)
            print(f'newer_url: {newer_url}')
            git_clone = f'git clone {newer_url}'
        try:
            subprocess.run(create_dir.split())
            os.chdir(new_key)
            subprocess.run(git_clone.split())
        except:
            raise

def get_argument_parser():
    parser = argparse.ArgumentParser(description='clone github repos to create a workspace or generate a metadata from existing workspace')

    sub_parsers = parser.add_subparsers(dest='subparser', help=
                                        'pass positional parameter : metadata or workspace', required=True)
    sub_parsers_metadata = sub_parsers.add_parser('metadata', help=
                                                    'metadata for Genarating metadata file for workspace that exists')
    sub_parsers_workspace = sub_parsers.add_parser('workspace', help=
                                                    'workspace for creating workspace from given metadata file')

    sub_parsers_metadata.add_argument('--workspaceDir', required=True, help='full path to workspace directory.')
    sub_parsers_metadata.add_argument('--metadata_file_name', required=True, help='name (not path) for metadata file (json). Will be created at root directory of this repo.')

    sub_parsers_workspace.add_argument('--file', required=True, help='full path of metadata fie.')
    sub_parsers_workspace.add_argument('--dirPath', required=True, help='local dir where tou want to setup workspace.') 

    return parser

def main(args):
    dict = {}
    src_file_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../'))

    parsed_args = get_argument_parser().parse_args(args)

    # get list of dirs
    if parsed_args.subparser == 'metadata':
        print(f'generating metadata file for {parsed_args.metadata_file_name}')
        json_dict = generatefile(parsed_args.workspaceDir)

        if json_dict:
            print(json.dumps(json_dict, indent=4))
            print(f'also written to: {os.path.join(src_file_dir, parsed_args.metadata_file_name)}')
            write_json_file(src_file_dir, json_dict, parsed_args.metadata_file_name)

    
    elif parsed_args.subparser == 'workspace':
        print(f'Creating workspace from given Metadata file: {parsed_args.file}')
        with open(parsed_args.file, 'r+') as robj:
            dict = json.load(robj)
        print(parsed_args.dirPath)
        create_workspace(dict, parsed_args.dirPath)


if __name__ == '__main__':
    main(sys.argv[1:])
