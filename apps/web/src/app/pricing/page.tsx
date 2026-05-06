import type { Metadata } from "next"
import { MarketingPage } from "@/components/layout/marketing-page"

export const metadata: Metadata = {
  title: "Pricing | InfraMind AI",
  description: "Explore InfraMind AI pricing models for individual engineers, platform teams, and enterprise infrastructure review workflows.",
}

const sections = [
  {
    title: "Starter",
    description:
      "Designed for individual engineers and small cloud teams who need rapid feedback on Terraform, CloudFormation, and Kubernetes changes before merge or deployment.",
  },
  {
    title: "Team",
    description:
      "Adds shared workspaces, more frequent analysis runs, richer reporting, and collaboration features so platform, security, and cost teams can review the same findings in one place.",
  },
  {
    title: "Enterprise",
    description:
      "Supports policy customization, environment segregation, compliance workflows, and rollout controls for organizations with larger infrastructure estates and stricter governance needs.",
  },
  {
    title: "Consumption Model",
    description:
      "Pricing can be aligned to volume, team size, or deployment scope so organizations can match the platform to how they review infrastructure changes across environments.",
  },
]

export default function PricingPage() {
  return (
    <MarketingPage
      eyebrow="Pricing"
      title="Pricing shaped around the way your infrastructure team ships."
      description="InfraMind AI supports evaluation paths for individual operators, collaborative platform teams, and enterprise change programs. Choose the rollout model that matches your analysis volume, governance needs, and review cadence."
      sections={sections}
      ctaLabel="Request Pricing Details"
      ctaHref="/contact"
    />
  )
}