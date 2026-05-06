/**
 * InfraMind AI — Lambda API handler
 *
 * Entry point for the AWS Lambda function serving the HTTP API.
 * API Gateway (HTTP API v2) proxies all requests to this handler.
 */

"use strict";

/**
 * @param {import('aws-lambda').APIGatewayProxyEventV2} event
 * @param {import('aws-lambda').Context} context
 * @returns {Promise<import('aws-lambda').APIGatewayProxyResultV2>}
 */
exports.handler = async (event, context) => {
  const { rawPath, requestContext } = event;
  const method = requestContext?.http?.method ?? "UNKNOWN";

  // Health check endpoint
  if (rawPath === "/health" || rawPath === "/api/health") {
    return {
      statusCode: 200,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        status: "ok",
        environment: process.env.NODE_ENV,
        requestId: context.awsRequestId,
        timestamp: new Date().toISOString(),
      }),
    };
  }

  // Default response — replace with your actual routing logic
  return {
    statusCode: 200,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: "InfraMind AI API",
      path: rawPath,
      method,
    }),
  };
};
