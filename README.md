#Mirage

Mirage is a simple blogging system that is 'serverless', similar to Jekyll. It will take Markdown files and build them into a site for you to deploy how you choose. It also has a built in mechanism to deploy to S3.

##Installation

Make sure you have Python, with `pip` and `virtualenv` installed. If you don't, you can read instructions for installing [pip](https://packaging.python.org/installing/) and [virtualenv](https://virtualenv.pypa.io/en/stable/installation/) here.

With these installed, simply run `./setup`.

##Writing

Before you start, modify your `config.yml` file's blog title and subtitle. You don't need to worry about the other values unless you plan to use the deploy functionality.

To write posts, simply create Markdown files in the `posts` directory. To create pages (static pages like, e.g. `/about`), do the same in the pages directory.

##Creating your site

When you're ready to publish, run `./mirage compile`. This will create a `site` directory, the contents of which you can put wherever you like. You can check it out locally by just opening `index.html`.

If you want to recompile the site whenever you change a file (e.g. if you are tweaking styles or javascript), run `./mirage watch`. 

##Deploying your site

Mirage can deploy to a number of cloud providers, including Amazon S3, Azure Blobs, Google Storage, and others.

You will need to get an access-key (or username) and a secret-key (or password) for your service, and add them to `config.yml`. You will also need to add the provider type, which may include a region. A full list of provider types supported is available [on libcloud](https://github.com/apache/libcloud/blob/trunk/libcloud/storage/providers.py). For some services, e.g. S3, you may need to select an appropriate provider for your region, e.g. `S3_EU_WEST`.

You will also need to configure the container name. Mirage will try and create a container with this name if it does not exist already.

You can then run `./mirage deploy` to push the site directly to the container. Additional configuration may be required to enable your service to be accessible as a static website, but Mirage will try and do it for you if possible.
