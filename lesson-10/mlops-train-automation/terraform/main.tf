locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Lesson      = "lesson-10"
  }
}

resource "aws_iam_role" "lambda" {
  name = "${var.project_name}-${var.environment}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "validate" {
  function_name    = "${var.project_name}-${var.environment}-validate"
  role             = aws_iam_role.lambda.arn
  handler          = "validate.handler"
  runtime          = "python3.12"
  filename         = "${path.module}/lambda/validate.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda/validate.zip")
  timeout          = 30

  tags = local.common_tags
}

resource "aws_lambda_function" "log_metrics" {
  function_name    = "${var.project_name}-${var.environment}-log-metrics"
  role             = aws_iam_role.lambda.arn
  handler          = "log_metrics.handler"
  runtime          = "python3.12"
  filename         = "${path.module}/lambda/log_metrics.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda/log_metrics.zip")
  timeout          = 30

  tags = local.common_tags
}

resource "aws_iam_role" "step_functions" {
  name = "${var.project_name}-${var.environment}-sfn-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "step_functions_invoke_lambda" {
  name = "${var.project_name}-${var.environment}-invoke-lambda"
  role = aws_iam_role.step_functions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.validate.arn,
          aws_lambda_function.log_metrics.arn
        ]
      }
    ]
  })
}

resource "aws_sfn_state_machine" "training_pipeline" {
  name     = "${var.project_name}-${var.environment}-pipeline"
  role_arn = aws_iam_role.step_functions.arn

  definition = jsonencode({
    Comment = "Simplified ML training automation workflow"
    StartAt = "ValidateData"
    States = {
      ValidateData = {
        Type     = "Task"
        Resource = aws_lambda_function.validate.arn
        Next     = "LogMetrics"
      }
      LogMetrics = {
        Type     = "Task"
        Resource = aws_lambda_function.log_metrics.arn
        End      = true
      }
    }
  })

  tags = local.common_tags
}
