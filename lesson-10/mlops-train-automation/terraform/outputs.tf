output "state_machine_arn" {
  description = "ARN of the Step Functions state machine."
  value       = aws_sfn_state_machine.training_pipeline.arn
}

output "manual_start_command" {
  description = "Command for manual Step Function execution."
  value       = "aws stepfunctions start-execution --region ${var.aws_region} --state-machine-arn ${aws_sfn_state_machine.training_pipeline.arn} --name train-manual --input '{\"source\":\"manual\",\"dataset\":\"iris\"}' --profile ${var.aws_profile}"
}

output "validate_lambda_name" {
  description = "Validate Lambda function name."
  value       = aws_lambda_function.validate.function_name
}

output "log_metrics_lambda_name" {
  description = "Log metrics Lambda function name."
  value       = aws_lambda_function.log_metrics.function_name
}
