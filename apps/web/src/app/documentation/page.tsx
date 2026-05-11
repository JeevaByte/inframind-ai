import type { Metadata } from "next"
import { MarketingPage } from "@/components/layout/marketing-page"

export const metadata: Metadata = {
  title: "Documentation | infralint",
  description: "Read the infralint product documentation for onboarding, analysis workflows, reporting behavior, and integration guidance.",
}

const sections = [
  {
    title: "Getting Started",
    description:
      "Upload Terraform, CloudFormation, or Kubernetes manifests, trigger analysis, and review categorized findings by severity, file, and recommendation from a single results screen.",
  },
  {
    title: "Analysis Workflow",
    description:
      "The current workflow supports file upload, automated analysis execution, and results review with summary metrics for security, compliance, and cost-related findings.",
  },
  {
    title: "Export and Sharing",
    description:
      "Analysis runs can be shared through a results link and exported into a generated PDF report for handoff, audit review, or offline documentation.",
  },
  {
    title: "API and Integration",
    description:
      "infralint can be connected to backend analysis services, CI checks, and policy automation paths so infrastructure review becomes part of the standard delivery workflow.",
  },
]

export default function DocumentationPage() {
  return (
    <MarketingPage
      eyebrow="Documentation"
      title="Documentation for teams shipping infrastructure with more confidence."
      description="Use the documentation hub as the reference point for onboarding, analysis workflow setup, reporting behavior, and future integration points across the infralint platform."
      sections={sections}
      ctaLabel="Open Upload Flow"
      ctaHref="/upload"
    />
  )
}