#Mirage

Mirage is a simple blogging system that is 'serverless', similar to Jekyll. It will take Markdown files and build them into a site for you to deploy how you choose. It also has a built in mechanism to deploy to S3.

##Installation

Make sure you have Python, with `pip` and `virtualenv` installed. If you don't, you can read instructions for installing [pip](https://packaging.python.org/installing/) and [virtualenv](https://virtualenv.pypa.io/en/stable/installation/) here.

With these installed, simply run `./setup`.

##Writing

Before you start, modify your `config.py` file's blog title and subtitle. You don't need to worry about the other values unless you plan to deploy with S3.

To write posts, simply create Markdown files in the `posts` directory. To create pages (static pages like, e.g. `/about`), do the same in the pages directory.

##Creating your site

When you're ready to publish, run `./mirage compile`. This will create a `site` directory, the contents of which you can put wherever you like. You can check it out locally by just opening `index.html`.

If you want to recompile the site whenever you change a file (e.g. if you are tweaking styles or javascript), run `./mirage watch`. 

##Deploying your site with S3

If you have set up an S3 bucket, create an AWS IAM user (there is a sample IAM policy in the `doc` directory), and add its `credentials.csv` to the project root, and the bucket name in `config.py`. You may need to set your AWS region too, e.g. `us-east-1`. There is a [full list of region codes on Amazon](http://docs.aws.amazon.com/general/latest/gr/rande.html#s3_region) if you're not sure what it should be.

You can then run `./mirage deploy-s3` to push the site directly to the S3 bucket.
