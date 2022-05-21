provider aws {
  region = "us-east-1"
}

resource "aws_s3_bucket" "packets" {
  bucket      = var.domain_name_packets

  tags = {
    Paskirtis = "packets_capture_project"
  }
}

resource "aws_s3_bucket" "packets_web" {
  bucket      = var.domain_name_packets_web
  acl = "public-read"
  policy = data.aws_iam_policy_document.website_policy.json
  website {
    index_document = "index.html"
    error_document = "index.html"
  }

  tags = {
    Paskirtis = "packets_capture_project"
  }
}

data "aws_iam_policy_document" "website_policy" {
  statement {
    actions = [
      "s3:GetObject"
    ]
    principals {
      identifiers = ["*"]
      type = "AWS"
    }
    resources = [
      "arn:aws:s3:::${var.domain_name_packets_web}/*"
    ]
  }
}


resource "aws_s3_bucket_acl" "example" {
  bucket = aws_s3_bucket.packets.id
  acl    = "private"
}

resource "aws_iam_role" "iam_for_lambda" {
  name = "iam_for_lambda"

  assume_role_policy = file("lambda-role-policy.json")

}


resource "aws_lambda_function" "main_lambda" {

  filename      = "deployment-package/my-deployment-package2.zip"
  function_name = "sagemaker-lambda"
  role          = aws_iam_role.iam_for_lambda.arn
  handler       = "lambda_function_script.lambda_handler"
  runtime       = "python3.8"
  memory_size   = 512

  environment {
    variables = {
      ENDPOINT_NAME = "blazingtext-2022-05-15-05-52-20-920"
      BUCKET_NAME   = "packets-bucket-web"
      FILE_LOCATION = "web_display/data.json"
    }
  }
}

resource "aws_lambda_permission" "S3_invoke_lambda" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main_lambda.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.packets.arn
}


resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.packets.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.main_lambda.arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".csv"
  }

  depends_on = [aws_lambda_permission.S3_invoke_lambda]
}
