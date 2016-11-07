![](resources/img/mirage.jpg)

> *A Highway Mirage* by [Michael Gil on Flickr](https://flic.kr/p/a8Koki) - [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/)

Welcome to the Mirage blogging engine. To write posts or pages, just create new Markdown files in the posts or pages folders.

To build the blog, run `./mirage compile`, and to deploy it to S3, make sure you have a `credentials.xml` file in the project, then run `./mirage deploy-s3`.

You can recompile live on file changes with `./mirage watch`.