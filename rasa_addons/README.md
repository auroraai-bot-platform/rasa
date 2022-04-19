# Rasa add-ons

This directory contains Botfront and Aurora specific add-ons for rasa.

## S3

This module provides function load_s3_language_models() which loads
pre-trained language models from s3 bucket. The functionality can be
triggered by giving option `--load-s3-language-models` to rasa. The
following envinronment variables must be defined:
* LANGUAGE_MODEL_S3_BUCKET: s3 bucket used for download
* LANGUAGE_MODEL_S3_DIR: s3 bucket directory whose all files are
  downloaded recursively
* LANGUAGE_MODEL_LOCAL_DIR: local directory to which the files are downloaded

For example, if we have bucket `rasa-model-files` that contains following files
```
language-models/file1
language-models/dir/file2
```

and rasa is triggered with the following environment variables:
```
LANGUAGE_MODEL_S3_BUCKET=rasa-model-files
LANGUAGE_MODEL_S3_DIR=language-models/
LANGUAGE_MODEL_LOCAL_DIR: /app/models
```

the following files will be created on the local side:
```
/app/models/language-models/file1
/app/models/language-models/dir/file2
```
