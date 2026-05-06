import type { Metadata } from "next"
import { MarketingPage } from "@/components/layout/marketing-page"

export const metadata: Metadata = {
  title: "Privacy | InfraMind AI",
  description: "Review the InfraMind AI privacy overview for uploaded infrastructure data, storage expectations, and operational transparency.",
}

const sections = [
  {
    title: "Data Handling",
    description:
      "Infrastructure files uploaded for analysis may contain configuration details that teams treat as sensitive. Privacy controls should therefore be clear, minimal, and aligned to the operational needs of the review workflow.",
  },
  {
    title: "Analysis Scope",
    description:
      "Analysis should be limited to the files and metadata necessary to generate findings, summaries, and downloadable reports. Extra collection beyond that scope should be avoided unless clearly disclosed.",
  },
  {
    title: "Access and Retention",
    description:
      "Teams evaluating the product should understand where uploaded files are stored, how long results are retained, and which users or systems are allowed to access them.",
  },
  {
    title: "Operational Transparency",
    description:
      "This page serves as the current public privacy placeholder. If the product is commercialized or used broadly, it should be replaced with a legal-reviewed policy tailored to the real storage and processing model.",
  },
]

export default function PrivacyPage() {
  return (
    <MarketingPage
      eyebrow="Privacy"
      title="A privacy stance that matches the sensitivity of infrastructure data."
      description="InfraMind AI is built around analyzing operational configuration files, so privacy expectations need to be explicit about what is uploaded, what is stored, and how results are handled."
      sections={sections}
      ctaLabel="Review Terms"
      ctaHref="/terms"
    />
  )
}