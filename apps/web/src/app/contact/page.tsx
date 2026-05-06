import type { Metadata } from "next"
import { ContactForm } from "@/components/contact/contact-form"
import { MarketingPage } from "@/components/layout/marketing-page"

export const metadata: Metadata = {
  title: "Contact | InfraMind AI",
  description: "Contact the InfraMind AI team about rollout, integration, pricing, and infrastructure review implementation details.",
}

const sections = [
  {
    title: "Sales and Evaluation",
    description:
      "Reach out when you want to discuss team rollout, pricing structure, or how InfraMind AI could fit into existing platform engineering and governance processes.",
  },
  {
    title: "Technical Questions",
    description:
      "Use the contact path to raise questions about supported file formats, backend integration points, deployment expectations, or reporting workflows.",
  },
  {
    title: "Partnerships",
    description:
      "If you are exploring workflow integration, platform partnerships, or joint infrastructure review capabilities, the contact channel is the right starting point.",
  },
  {
    title: "Response Path",
    description:
      "For now, treat this page as the public contact destination for product and implementation discussions. A dedicated form or support workflow can be added next.",
  },
]

export default function ContactPage() {
  return (
    <MarketingPage
      eyebrow="Contact"
      title="Talk to the team about rollout, integration, or implementation details."
      description="InfraMind AI can support different adoption paths depending on your stack, review workflow, and governance requirements. Use this page as the starting point for that conversation."
      sections={sections}
      ctaLabel="Start an Analysis"
      ctaHref="/upload"
    >
      <ContactForm />
    </MarketingPage>
  )
}