import type { Metadata } from "next"
import { MarketingPage } from "@/components/layout/marketing-page"

export const metadata: Metadata = {
  title: "Blog | infralint",
  description: "Read infralint perspectives on infrastructure review, policy automation, cost awareness, and platform workflows.",
}

const sections = [
  {
    title: "From Static Files to Actionable Findings",
    description:
      "A walkthrough of how infrastructure definitions can be transformed into issue summaries, severity distributions, and recommended remediations that teams can act on quickly.",
  },
  {
    title: "Designing Review Workflows for Platform Teams",
    description:
      "An exploration of how platform engineering and security teams can standardize review expectations across Terraform, CloudFormation, and Kubernetes artifacts.",
  },
  {
    title: "Making Cost Review Part of Delivery",
    description:
      "A practical look at shifting cost-awareness earlier in the delivery cycle instead of waiting until cloud spend reviews at the end of the month.",
  },
  {
    title: "Operationalizing Infrastructure Reports",
    description:
      "Guidance for turning analysis outputs into dashboards, handoff artifacts, and review rituals that can fit naturally into modern engineering workflows.",
  },
]

export default function BlogPage() {
  return (
    <MarketingPage
      eyebrow="Blog"
      title="Notes, patterns, and product thinking from the infralint workflow."
      description="The blog is where we capture ideas about infrastructure review, policy automation, developer ergonomics, and what it takes to make analysis useful in everyday engineering work."
      sections={sections}
      ctaLabel="Read the Product Overview"
      ctaHref="/about"
    />
  )
}