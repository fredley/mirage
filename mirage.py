#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import argh
import shutil
import os
import time
import uglipyjs

from boto.s3 import connect_to_region
from boto.s3.connection import OrdinaryCallingFormat
from boto.s3.key import Key
from csscompressor import compress
from markdown import markdown
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from config import *

# Set up directory structure
project_root = os.path.dirname(__file__)
posts_dir = os.path.join(project_root, "posts")
pages_dir = os.path.join(project_root, "pages")
resources_dir = os.path.join(project_root, "resources")

build_dir = os.path.join(project_root, "site")
build_posts_dir = os.path.join(build_dir, "posts")
build_resources_dir = os.path.join(build_dir, "resources")


class cnsl:
  """
  Utility class for formatting print statements
  """
  HEADER = '\033[95m'
  OKBLUE = '\033[94m'
  OKGREEN = '\033[92m'
  WARNING = '\033[93m'
  FAIL = '\033[91m'
  ENDC = '\033[0m'
  BOLD = '\033[1m'
  UNDERLINE = '\033[4m'

  @staticmethod
  def success(msg):
    print(cnsl.OKGREEN, '✔', cnsl.ENDC, msg)

  @staticmethod
  def ok(msg):
    print(cnsl.OKBLUE, '>', cnsl.ENDC, msg)

  @staticmethod
  def warn(msg):
    print(cnsl.WARNING, '!', cnsl.ENDC, msg)

  @staticmethod
  def error(msg):
    print(cnsl.FAIL, '✘', cnsl.ENDC, msg)

def chunks(l, n):
    """
      Yield successive n-sized chunks from l. Used for pagination.
      http://stackoverflow.com/a/312464/319618
    """
    for i in xrange(0, len(l), n):
        yield l[i:i + n]

def load_posts(directory, mode="post"):
  for filename in os.listdir(directory):
    post_filename = os.path.join(directory, filename)
    with open(post_filename) as post_file:
      split_filename = os.path.splitext(filename)
      if len(split_filename) == 2 and split_filename[1] == ".md":
        cnsl.ok("Compiling {} {}".format(mode,filename))
        post_slug = split_filename[0].lower().replace(" ","-")
        new_filename = os.path.join(post_slug, "index.html")
        url = "/" + os.path.join("posts", post_slug) if mode == "post" else "/" + post_slug
        content = markdown(post_file.read())
        yield {
          'filename': new_filename,
          'url': url,
          'post-title': split_filename[0],
          'content': content,
          'date': time.ctime(os.path.getctime(post_filename))
        }
      else:
        cnsl.warn("Ignoring file " + filename)

def write_posts(base_dir, posts, templates):
  for post in posts:
    full_path = os.path.join(base_dir, post['filename'])
    os.makedirs(os.path.split(full_path)[0])
    with open(full_path, "w") as published:
      cnsl.success("Writing post " + post['filename'])
      write_template(published, post, templates)

def render_post(template, post):
  return (template
  .replace("{{content}}", post["content"])
  .replace("{{permalink}}", post["url"])
  .replace("{{post-title}}", post["post-title"])
  .replace("{{post-date}}", post["date"]))

def write_template(file, post, templates):
  file.write(templates["base"]
    .replace("{{posts}}", render_post(templates["post"], post))
    .replace("{{pagination}}",""))

def page_url(n):
  return "/" if n == 1 else "/" + str(n)

def render_pages(total_pages, current_page):
  if total_pages == 1:
    return ''
  pages_string = '<a href="{}">&lt; Newer</a> &bull; '.format(page_url(current_page - 1)) if current_page > 1 else '' 
  for i in xrange(1,total_pages + 1):
    if current_page == i:
      pages_string += str(i) + " "
    else:
      pages_string += '<a href="{}">{}</a> '.format(page_url(i), i)

  pages_string += ' &bull; <a href="{}">Older &gt;</a>'.format(page_url(current_page + 1)) if current_page < total_pages else ''
  return pages_string

def move_resource(file, filename, filetype, compile_function=lambda x: x):
  split_filename = os.path.splitext(filename)
  if split_filename[0][-4:] == ".min":
    new_filename = filename
  else:
    new_filename = split_filename[0] + ".min." + filetype
  with open(os.path.join(build_resources_dir, filetype, new_filename), "w") as published:
    if split_filename[0][-4:] == ".min":
      cnsl.success("Copying minified {} file: {}".format(filetype, filename))
      published.write(file.read())
    else:
      cnsl.success("Minifying {} file: {}".format(filetype, filename))
      published.write(compile_function(file.read()))
    return new_filename

def move_image(file, filename):
  with open(os.path.join(build_resources_dir, "img", filename), "w") as published:
      cnsl.success("Copying image file: {}".format(filename))
      published.write(file.read())

def compile():

  cnsl.ok("Compiling project")
  try:
    shutil.rmtree(build_dir)
  except:
    pass
  os.mkdir(build_dir)
  os.mkdir(build_posts_dir)
  os.mkdir(build_resources_dir)
  os.mkdir(os.path.join(build_resources_dir,"css"))
  os.mkdir(os.path.join(build_resources_dir,"js"))
  os.mkdir(os.path.join(build_resources_dir,"img"))

  templates = {}

  for filename in os.listdir(os.path.join(project_root, "templates")):
    split_filename = os.path.splitext(filename)
    with open(os.path.join(project_root, "templates", filename)) as template_file:
      cnsl.ok("Loading template {}".format(filename))
      templates[split_filename[0]] = template_file.read()

  if "base" in templates and "post" in templates:
    cnsl.success("All required templates found")
  else:
    cnsl.error("Missing templates")
    return

  # Compile and minify resources
  resources = {
    "js": [],
    "css": []
  }

  for root, dirs, files in os.walk(resources_dir):
    for filename in files:
      split_filename = os.path.splitext(filename)
      ext = split_filename[1].lower()
      if len(split_filename) == 2:
        with open(os.path.join(root, filename)) as resource_file:
          if ext == ".js":
            resources["js"].append(move_resource(resource_file, filename, "js", uglipyjs.compile))
          elif ext == ".css":
            resources["css"].append(move_resource(resource_file, filename, "css", compress))
          elif ext[1:] in ["jpg", "jpeg", "png", "gif"]:
            move_image(resource_file, filename)
          else:
            cnsl.warn("Don't know what to do with file {}".format(filename))

  # Generate style resources
  style_headers = ''.join(['<link href="/resources/css/{}" rel="stylesheet">'.format(name)
   for name in resources["css"]])

  # Generate script resources
  script_headers = ''.join(['<script src="/resources/js/{}"></script>'.format(name)
   for name in resources["js"]])

  # Update base template
  templates["base"] = templates["base"].replace(
    "{{styles}}", style_headers).replace(
    "{{scripts}}", script_headers).replace(
    "{{title}}", BLOG_TITLE).replace(
    "{{subtitle}}", BLOG_SUBTITLE)

  # Compile posts and pages

  pages = list(load_posts(pages_dir, mode="page"))
  posts = list(load_posts(posts_dir, mode="post"))

  # update pages links on base template

  pages_links = ''.join(['<li class="nav-item"><a class="pure-button" href="{}">{}</a></li>' \
    .format(page["url"], page["post-title"]) for page in pages])

  templates["base"] = templates["base"].replace("{{pages}}", pages_links)

  # write out pages files

  write_posts(build_dir, pages, templates)

  write_posts(build_posts_dir, posts, templates)

  # Make a list of recent posts
  posts.sort(key=lambda x: x["date"], reverse=True)
  cs = list(chunks(posts,10))
  i = 1
  for chunk in cs:
    posts_chunk = ''.join([render_post(templates["post"], post) for post in chunk])
    # Write out index file
    if i == 1:
      filename = "index.html"
    else:
      filename = os.path.join(str(i), "index.html")
      os.makedirs(os.path.join(build_dir, str(i)))
    with open(os.path.join(build_dir, filename), "w") as index_file:
      index_file.write(templates["base"]
        .replace("{{posts}}", posts_chunk)
        .replace("{{pagination}}", render_pages(len(cs), i)))
    cnsl.success("Wrote index file")
    i += 1

class ReloadHandler(FileSystemEventHandler):
    def on_modified(self, event):
      split_filename = os.path.splitext(event.src_path)
      if event.src_path[:8] != "./build/" \
        and len(split_filename) == 2 \
        and split_filename[1][1:] in ["html", "css", "js", "md"]:
        cnsl.warn("Source file {} changed, recompiling...\n".format(event.src_path))
        try:
          compile()
        except Exception as e:
          cnsl.error("Something went wrong trying to compile: " + e)
      else:
        cnsl.warn("Ignoring change in file {}".format(event.src_path))

def watch():
  compile()
  cnsl.ok("Watching for file changes\n")
  observer = Observer()
  observer.schedule(ReloadHandler(), ".", recursive=True)
  observer.start()
  try:
    while True:
      time.sleep(1)
  except KeyboardInterrupt:
    observer.stop()
    cnsl.ok("Stopped watching for file changes")
  observer.join()

def deploy_s3():
  compile()
  if not os.path.exists(os.path.join(project_root, "credentials.csv")):
    cnsl.error("You must add a credentials.csv from AWS to your project.")
    return
  with open(os.path.join(project_root, "credentials.csv")) as credentials_file:
    credentials = credentials_file.read()
  access_key = credentials.split("\n")[1].split(",")[1]
  secret_key = credentials.split("\n")[1].split(",")[2]
  try:
    s3 = connect_to_region(
      aws_access_key_id=access_key, 
      aws_secret_access_key=secret_key, 
      region_name=AWS_REGION, 
      calling_format=OrdinaryCallingFormat())
    cnsl.success("Connected to S3")
  except:
    cnsl.error("Could not connect to AWS, are your permissions set up ok?")
    return
  try:
    bucket = s3.get_bucket(S3_BUCKET)
    cnsl.success("Loaded bucket {}".format(S3_BUCKET))
  except:
    cnsl.error("Could not load bucket {}, are your permissions set up ok?".format(S3_BUCKET))
    return
  for root, dirs, files in os.walk(build_dir):
    for filename in files:
      full_filename = os.path.join(root, filename)
      file_key = Key(bucket)
      file_key.key = full_filename[5:] # Remove build/
      file_key.set_contents_from_filename(full_filename, policy='public-read')
      cnsl.success("Uploaded " + full_filename[5:])
  cnsl.success("Site successfully uploaded to S3 bucket {}".format(S3_BUCKET))


# CLI

parser = argh.ArghParser()
#todo deploy (S3)
parser.add_commands([compile, watch, deploy_s3])

if __name__ == '__main__':
  parser.dispatch()
