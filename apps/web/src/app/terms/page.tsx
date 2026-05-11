import type { Metadata } from "next"
import { MarketingPage } from "@/components/layout/marketing-page"

export const metadata: Metadata = {
  title: "Terms | infralint",
  description: "Review the infralint terms overview for platform use, analysis outputs, accountability, and document status.",
}

const sections = [
  {
    title: "Platform Use",
    description:
      "infralint is intended for infrastructure review, reporting, and workflow experimentation. Teams using the platform remain responsible for validating and approving infrastructure changes before production use.",
  },
  {
    title: "Analysis Output",
    description:
      "Findings, scores, and recommendations are decision-support artifacts. They should guide review conversations, but they should not be treated as a substitute for engineering judgment or change management controls.",
  },
  {
    title: "Accountability",
    description:
      "Organizations remain accountable for the correctness, legality, and operational safety of the infrastructure changes they submit to or export from the platform.",
  },
  {
    title: "Document Status",
    description:
      "This page is a product placeholder for terms content and should be replaced with a formal, legal-reviewed terms document before broad external release or customer onboarding.",
  },
]

export default function TermsPage() {
  return (
    <MarketingPage
      eyebrow="Terms"
      title="Usage terms that reflect the reality of infrastructure decision support."
      description="infralint helps surface risks and recommendations, but teams still own the final decision to apply changes and the operating consequences of those changes."
      sections={sections}
      ctaLabel="Review Privacy"
      ctaHref="/privacy"
    />
  )
}