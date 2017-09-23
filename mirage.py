#!/usr/bin/env python

import argh
import shutil
import os
import posixpath
import http.server
import socketserver
import threading
import time
import uglipyjs
import urllib.request, urllib.parse, urllib.error
import webbrowser
import yaml

from csscompressor import compress
from libcloud.storage.types import Provider, ContainerDoesNotExistError
from libcloud.storage.providers import get_driver
from markdown import markdown
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from src.cnsl import cnsl

try:
  with open("config.yml") as config_yml:
    config = yaml.load(config_yml.read())
except Exception as e:
  config = {}

# Set up directory structure
blog_root = os.path.dirname(__file__)
posts_dir = os.path.join(blog_root, "posts")
pages_dir = os.path.join(blog_root, "pages")
resources_dir = os.path.join(blog_root, "resources")

build_dir = os.path.join(blog_root, "site")
build_posts_dir = os.path.join(build_dir, "posts")
build_resources_dir = os.path.join(build_dir, "resources")


def chunks(l, n):
  """
  Yield successive n-sized chunks from l. Used for pagination.
  http://stackoverflow.com/a/312464/319618
  """
  for i in range(0, len(l), n):
    yield l[i:i + n]


def load_posts(directory, mode="post"):
  for filename in os.listdir(directory):
    post_filename = os.path.join(directory, filename)
    with open(post_filename) as post_file:
      split_filename = os.path.splitext(filename)
      if len(split_filename) == 2 and split_filename[1] == ".md":
        if split_filename[1].endswith("_draft"):
          cnsl.warn("Skipping draft file {}".format(filename))
          continue
        cnsl.ok("Compiling {} {}".format(mode, filename))
        post_slug = split_filename[0].lower().replace(" ", "-")
        new_filename = os.path.join(post_slug, "index.html")
        url = "/" + \
            os.path.join(
              "posts", post_slug) if mode == "post" else "/" + post_slug
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
             .replace("{{pagination}}", ""))


def page_url(n):
  return "/" if n == 1 else "/" + str(n)


def render_pages(total_pages, current_page):
  if total_pages == 1:
    return ''
  pages_string = '<a href="{}">&lt; Newer</a> &bull; '.format(
      page_url(current_page - 1)) if current_page > 1 else ''
  for i in range(1, total_pages + 1):
    if current_page == i:
      pages_string += str(i) + " "
    else:
      pages_string += '<a href="{}">{}</a> '.format(page_url(i), i)

  pages_string += ' &bull; <a href="{}">Older &gt;</a>'.format(
      page_url(current_page + 1)) if current_page < total_pages else ''
  return pages_string


def move_resource(file, filename, filetype, compile_function=lambda x: x):
  split_filename = os.path.splitext(filename)
  if split_filename[0][-4:] == ".min":
    new_filename = filename
  else:
    new_filename = split_filename[0] + ".min." + filetype
  mode = "wb" if filetype == "js" else "w"
  with open(os.path.join(build_resources_dir, filetype, new_filename), mode) as published:
    if split_filename[0][-4:] == ".min":
      cnsl.success("Copying minified {} file: {}".format(filetype, filename))
      published.write(file.read())
    else:
      cnsl.success("Minifying {} file: {}".format(filetype, filename))
      published.write(compile_function(file.read()))
    return new_filename


def move_image(file, filename):
  with open(os.path.join(build_resources_dir, "img", filename), "wb") as published:
    cnsl.success("Copying image file: {}".format(filename))
    published.write(file.read())


def compile():
  """
  Compile the blog, outputting the result into /site.
  """

  cnsl.ok("Compiling blog")
  try:
    shutil.rmtree(build_dir)
  except:
    pass
  os.mkdir(build_dir)
  os.mkdir(build_posts_dir)
  os.mkdir(build_resources_dir)
  os.mkdir(os.path.join(build_resources_dir, "css"))
  os.mkdir(os.path.join(build_resources_dir, "js"))
  os.mkdir(os.path.join(build_resources_dir, "img"))

  templates = {}

  for filename in os.listdir(os.path.join(blog_root, "templates")):
    split_filename = os.path.splitext(filename)
    with open(os.path.join(blog_root, "templates", filename)) as template_file:
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
        if ext[1:] == "ico":
          with open(os.path.join(root, filename), "rb") as favicon:
            with open(os.path.join(build_dir, filename), "wb") as published:
              cnsl.success("Copying favicon file: {}".format(filename))
              published.write(favicon.read())
        elif ext[1:] in ["jpg", "jpeg", "png", "gif"]:
          with open(os.path.join(root, filename), "rb") as resource_file:
            move_image(resource_file, filename)
        elif ext == ".css":
          with open(os.path.join(root, filename), "r") as resource_file:
            resources["css"].append(
                move_resource(resource_file, filename, "css", compress))
        else:
          with open(os.path.join(root, filename)) as resource_file:
            if ext == ".js":
              resources["js"].append(
                  move_resource(resource_file, filename, "js", uglipyjs.compile))
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
      "{{title}}", config["blog-title"]).replace(
      "{{subtitle}}", config["blog-subtitle"])

  # Compile posts and pages

  pages = list(load_posts(pages_dir, mode="page"))
  posts = list(load_posts(posts_dir, mode="post"))

  # update pages links on base template

  pages_links = ''.join(['<li class="page-link"><a class="pure-button" href="{}">{}</a></li>'
                         .format(page["url"], page["post-title"]) for page in pages])

  templates["base"] = templates["base"].replace("{{pages}}", pages_links)

  # write out pages files

  write_posts(build_dir, pages, templates)
  write_posts(build_posts_dir, posts, templates)

  # Make a list of recent posts
  posts.sort(key=lambda x: x["date"])
  cs = list(chunks(posts, 10))
  i = 1
  for chunk in cs:
    posts_chunk = ''.join(
        [render_post(templates["post"], post) for post in chunk])
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
      cnsl.warn(
          "Source file {} changed, recompiling...\n".format(event.src_path))
      try:
        compile()
      except Exception as e:
        cnsl.error("Something went wrong trying to compile: " + e)
    else:
      cnsl.warn("Ignoring change in file {}".format(event.src_path))


class SiteHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):

  def translate_path(self, path):
    """ This is an old-style class, so can't super :-( """
    path = posixpath.normpath(urllib.parse.unquote(path))
    words = path.split('/')
    words = [_f for _f in words if _f]
    path = "site"
    for word in words:
      drive, word = os.path.splitdrive(word)
      head, word = os.path.split(word)
      if word in (os.curdir, os.pardir):
        continue
      path = os.path.join(path, word)
    return path


def watch():
  """
  Recompile the blog any time a file changes.
  """
  compile()
  cnsl.ok("Watching for file changes")
  observer = Observer()
  observer.schedule(ReloadHandler(), ".", recursive=True)
  observer.start()
  port = config.get("port", 8000)
  socketserver.TCPServer.allow_reuse_address = True
  httpd = socketserver.TCPServer(("", port), SiteHTTPRequestHandler)
  http = threading.Thread(target=httpd.serve_forever)
  cnsl.ok("Starting webserver on port {}".format(port))
  http.start()
  webbrowser.open("http://localhost:{}/".format(port))
  try:
    while True:
      time.sleep(1)
  except KeyboardInterrupt:
    observer.stop()
    httpd.shutdown()
    cnsl.ok("Stopped webserver on port {}".format(port))
    cnsl.ok("Stopped watching for file changes")
  http.join()
  observer.join()


def deploy():
  """
  Deploy your site to a cloud service.
  You must have specified a service provider, container name,
  and access credentials in config.yml,
  """
  compile()

  try:
    service = config["deploy"]["service"]
  except:
    cnsl.error("You must specify a service to deploy to in config.yml")
    return

  try:
    CloudFiles = get_driver(getattr(Provider, service))
  except:
    cnsl.error(
        "The storage provider config is not valid. The available providers are as follows:")
    cnsl.error(
        ', '.join([name for name in list(vars(Provider).keys()) if name[:2] != "__"]))
    return

  try:
    driver = CloudFiles(
        config["deploy"]["access-key"], config["deploy"]["secret-key"])
  except Exception as e:
    cnsl.error("Could not connect to storage service because: {}".format(e))
    return

  try:
    container = driver.get_container(
        container_name=config["deploy"]["container-name"])
    cnsl.success("Loaded container {} from {}".format(
        container.name, container.driver.name))
  except ContainerDoesNotExistError:
    cnsl.warn(
        "Could not load container {}, trying to create it".format(container.name))
    try:
      container = driver.create_container(container_name=container)
      cnsl.success("Created container {}".format(container.name))
    except Exception as e:
      cnsl.error("Could not create bucket because: {}".format(e))
      return
  except Exception as e:
    cnsl.error("Could not load container {} because: {}".format(
        config["deploy"]["container-name"], e))
    return

  # These operations are supported by some providers, so try each in turn
  try:
    driver.ex_enable_static_website(container=container)
    cnsl.success("Enabled static website hosting")
  except:
    cnsl.warn(
        "Could not enable static website hosting, you may have to do this manually")

  try:
    driver.enable_container_cdn(container=container)
    cnsl.success("Enabled cdn")
  except:
    cnsl.warn("Could not enable cdn, you may have to do this manually")

  # TODO driver.ex_set_error_page(container=container, file_name='error.html')

  for root, dirs, files in os.walk(build_dir):
    for filename in files:
      full_filename = os.path.join(root, filename)
      # Remove deploy directory prefix
      full_path = os.path.join(*full_filename.split(os.sep)[1:])
      if "S3" in container.driver.name:
        extra = {"acl": "public-read"}
      else:
        # TODO test with all other services
        extra = {}
      try:
        driver.upload_object(
            file_path=full_filename,
            container=container,
            extra=extra,
            object_name=full_path)
        cnsl.success("Uploaded " + full_path)
      except Exception as e:
        cnsl.error("Could not upload {}, because: {}".format(full_path, e))

  cnsl.success("Site successfully uploaded to container {} on {}".format(
      container.name, container.driver.name))

  try:
    cnsl.ok('All done you can view the website at: ' +
            driver.get_container_cdn_url(container=container))
  except:
    pass


def setup():
  """
  Setup your config.yml file interactively.
  """
  if os.path.exists('config.yml'):
    cnsl.warn("Setting up blog, but config file already exists")
    cnsl.warn("Existing config will be overwritten, or ctrl+c to exit")
  title = input(
      "\nPlease enter a title for your blog (you can change this later): \n")
  subtitle = input("\nPlease enter a subtitle for your blog: \n")
  with open('config.sample.yml') as sample_file:
    sample = sample_file.read()
  modified = ""
  for line in sample.split("\n"):
    if line.startswith("blog-title"):
      modified += 'blog-title: "{}"'.format(
          title.replace('\\', "\\\\").replace('"', '\\"'))
    elif line.startswith("blog-subtitle"):
      modified += 'blog-subtitle: "{}"'.format(
          subtitle.replace('\\', "\\\\").replace('"', '\\"'))
    else:
      modified += line
    modified += "\n"
  with open('config.yml', 'w') as config_file:
    config_file.write(modified)
  cnsl.success("Config file written")
  cnsl.ok("Welcome to Mirage. Write posts as markdown files in /posts.")
  cnsl.ok("Run ./mirage compile to compile your blog.")
  cnsl.ok("Run ./mirage help for more information.")

# CLI

parser = argh.ArghParser()
parser.add_commands([compile, watch, deploy, setup])
# parser.set_default_command(compile)

if __name__ == '__main__':
  cnsl.header()
  parser.dispatch()
