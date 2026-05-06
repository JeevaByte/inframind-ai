import type { Metadata } from "next"
import { MarketingPage } from "@/components/layout/marketing-page"

export const metadata: Metadata = {
  title: "About | InfraMind AI",
  description: "Learn what InfraMind AI builds for DevOps, platform, security, and cloud teams reviewing infrastructure changes.",
}

const sections = [
  {
    title: "What We Build",
    description:
      "InfraMind AI helps engineering teams inspect infrastructure definitions before changes reach production, with automated feedback on security posture, governance risk, and optimization opportunities.",
  },
  {
    title: "Who It Serves",
    description:
      "The product is intended for DevOps, platform, security, and cloud architecture teams who need a faster way to review infrastructure changes without losing context or traceability.",
  },
  {
    title: "Why It Matters",
    description:
      "Manual infrastructure review is slow and inconsistent. InfraMind AI aims to make the first pass of analysis immediate, structured, and repeatable across formats and cloud environments.",
  },
  {
    title: "How Teams Adopt It",
    description:
      "Teams can start with ad hoc uploads, expand to shared review workflows, and then connect analysis and reporting into their delivery pipelines as confidence grows.",
  },
]

export default function AboutPage() {
  return (
    <MarketingPage
      eyebrow="About"
      title="Built for teams that want infrastructure review to move at engineering speed."
      description="InfraMind AI brings together analysis, summarization, and reporting so infrastructure change review becomes easier to understand, easier to share, and easier to operationalize."
      sections={sections}
    />
  )
}