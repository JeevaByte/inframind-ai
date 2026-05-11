"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Avatar } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import {
  BarChart3,
  Shield,
  TrendingDown,
  Eye,
  Upload,
  FileText,
  ArrowRight,
  Sparkles,
  Radar,
  Bot,
} from "lucide-react"
import Link from "next/link"
import { motion } from "framer-motion"
import { MarketingFooter } from "@/components/layout/marketing-footer"

const features = [
  {
    title: "Infrastructure Analysis",
    description:
      "Analyze Terraform, CloudFormation, and Kubernetes configurations for misconfigurations and best practices.",
    icon: BarChart3,
  },
  {
    title: "Security Scanning",
    description:
      "Identify security vulnerabilities, overly permissive rules, and compliance violations.",
    icon: Shield,
  },
  {
    title: "Cost Optimization",
    description:
      "Find unused resources and rightsizing opportunities to reduce your cloud spending.",
    icon: TrendingDown,
  },
  {
    title: "Real-time Monitoring",
    description:
      "Continuous monitoring of your infrastructure with detailed issue tracking.",
    icon: Eye,
  },
]

const steps = [
  {
    number: "1",
    title: "Upload",
    description: "Upload your Terraform, CloudFormation, or Kubernetes files",
    icon: Upload,
  },
  {
    number: "2",
    title: "Analyze",
    description: "Our AI analyzes your infrastructure for issues and optimization opportunities",
    icon: BarChart3,
  },
  {
    number: "3",
    title: "Results",
    description: "Get detailed reports with recommendations and cost savings estimates",
    icon: FileText,
  },
]

const testimonials = [
  {
    name: "Sarah Chen",
    role: "DevOps Lead",
    quote: "infralint helped us identify $50k/month in unnecessary infrastructure costs.",
    initial: "SC",
  },
  {
    name: "Marcus Johnson",
    role: "Security Engineer",
    quote: "Found critical security issues we missed in our manual reviews. Invaluable tool.",
    initial: "MJ",
  },
  {
    name: "Priya Patel",
    role: "Cloud Architect",
    quote: "Saves our team hours every week. Highly recommend for any infrastructure team.",
    initial: "PP",
  },
]

const faqs = [
  {
    question: "What makes the UI workflow feel premium instead of just functional?",
    answer:
      "The core flows are tuned for fast infrastructure review, but the presentation is designed to feel intentional: stronger hierarchy, denser signal in the hero, and richer shadcn-style components for guidance instead of plain blocks of text.",
  },
  {
    question: "Does infralint only support static uploads?",
    answer:
      "The current product centers on upload-and-analyze flows, but the API and dashboard structure are already aligned with future CI ingestion, scheduled scans, and policy-driven review workflows.",
  },
  {
    question: "How should teams use the cost estimates?",
    answer:
      "Treat them as decision-support signals. The dashboard aggregates estimated savings from findings metadata so teams can prioritize remediation without waiting for month-end cloud reporting.",
  },
]

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.8 },
  },
}

export default function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Hero Section */}
      <section className="relative mx-auto max-w-7xl overflow-hidden px-4 py-20 sm:px-6 lg:px-8">
        <div className="absolute -top-40 right-0 h-96 w-96 rounded-full bg-primary/15 blur-3xl" />
        <div className="absolute bottom-0 left-0 h-96 w-96 rounded-full bg-accent/25 blur-3xl" />

        <motion.div
          className="relative grid gap-12 lg:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)] lg:items-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <div className="space-y-8 text-left">
            <div className="space-y-4">
              <Badge variant="outline" className="border-primary/20 bg-primary/5 px-4 py-1 text-primary">
                Review infra changes with an operator-grade lens
              </Badge>
              <h1 className="text-5xl font-bold tracking-tight text-foreground sm:text-6xl lg:text-7xl">
                infralint
              </h1>
              <p className="max-w-2xl text-lg leading-8 text-muted-foreground sm:text-xl">
                AI-assisted infrastructure analysis for Terraform, CloudFormation, Kubernetes, Dockerfiles, and GitHub Actions with stronger visual feedback, clearer priorities, and faster handoff-ready reporting.
              </p>
            </div>

            <Alert className="surface-panel hero-glow max-w-2xl">
              <Sparkles className="h-4 w-4" />
              <AlertTitle>Designed to feel like a control surface, not a marketing template</AlertTitle>
              <AlertDescription>
                Rich semantic tokens, stronger contrast, and higher-end shadcn components now carry the product story instead of plain text blocks.
              </AlertDescription>
            </Alert>

            <div className="flex flex-col gap-4 sm:flex-row">
              <Link href="/upload">
                <Button size="lg" className="gap-2 rounded-full px-7 hero-glow">
                  Start Analysis <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/dashboard">
                <Button size="lg" variant="outline" className="rounded-full border-border/70 bg-card/70 px-7 backdrop-blur-sm">
                  Open Dashboard
                </Button>
              </Link>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <div className="surface-panel rounded-3xl p-4">
                <Radar className="mb-3 h-5 w-5 text-primary" />
                <p className="text-sm font-semibold">Signal-first findings</p>
                <p className="mt-1 text-sm text-muted-foreground">Severity, score, and remediation context are visible immediately.</p>
              </div>
              <div className="surface-panel rounded-3xl p-4">
                <Bot className="mb-3 h-5 w-5 text-primary" />
                <p className="text-sm font-semibold">AI-backed summaries</p>
                <p className="mt-1 text-sm text-muted-foreground">Useful summaries without losing the raw infrastructure details.</p>
              </div>
              <div className="surface-panel rounded-3xl p-4">
                <TrendingDown className="mb-3 h-5 w-5 text-primary" />
                <p className="text-sm font-semibold">Operational cost signals</p>
                <p className="mt-1 text-sm text-muted-foreground">Surface likely savings before they show up in billing review.</p>
              </div>
            </div>
          </div>

          <div className="surface-panel rounded-[2rem] p-6 lg:p-7">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Mission Control</p>
                <h2 className="mt-2 text-2xl font-semibold">What teams remember</h2>
              </div>
              <Badge className="rounded-full px-3 py-1">Live Review</Badge>
            </div>

            <div className="grid gap-4">
              {[
                ["Critical drift prevented", "12 high-risk findings caught before merge"],
                ["Shared review context", "One report links architecture, security, and cost"],
                ["Faster decisions", "Teams move from raw YAML to prioritized actions quickly"],
              ].map(([title, text]) => (
                <Card key={title} className="rounded-3xl border-border/60 bg-background/60 shadow-none">
                  <CardContent className="flex items-start gap-4 p-5">
                    <div className="mt-1 h-2.5 w-2.5 rounded-full bg-primary" />
                    <div>
                      <p className="font-medium text-foreground">{title}</p>
                      <p className="mt-1 text-sm text-muted-foreground">{text}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </motion.div>
      </section>

      <Separator />

      {/* Features Section */}
      <section
        id="features"
        className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8"
      >
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <h2 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
            Powerful Features
          </h2>
          <p className="text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto">
            Everything you need to secure and optimize your infrastructure
          </p>
        </motion.div>

        <motion.div
          className="grid md:grid-cols-2 gap-8"
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          {features.map(({ title, description, icon: Icon }) => (
            <motion.div key={title} variants={itemVariants}>
              <Card className="surface-panel h-full rounded-[1.75rem] transition-shadow hover:shadow-2xl">
                <CardHeader>
                  <div className="flex items-start gap-4">
                    <div className="rounded-2xl bg-primary/10 p-3 text-primary">
                      <Icon className="h-6 w-6" />
                    </div>
                    <CardTitle className="text-xl">{title}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    {description}
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </section>

      <Separator />

      {/* How It Works Section */}
      <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <h2 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
            How It Works
          </h2>
          <p className="text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto">
            Three simple steps to analyze your infrastructure
          </p>
        </motion.div>

        <motion.div
          className="grid md:grid-cols-3 gap-8"
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          {steps.map(({ number, title, description, icon: Icon }, index) => (
            <motion.div key={number} variants={itemVariants}>
              <div className="relative">
                <Card className="surface-panel h-full rounded-[1.75rem]">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="mb-2 text-3xl font-bold text-primary">
                          {number}
                        </div>
                        <CardTitle>{title}</CardTitle>
                      </div>
                      <Icon className="h-8 w-8 text-muted-foreground" />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground">
                      {description}
                    </p>
                  </CardContent>
                </Card>
                {index < steps.length - 1 && (
                  <div className="hidden md:block absolute top-1/2 -right-4 transform -translate-y-1/2">
                    <ArrowRight className="h-8 w-8 text-border" />
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </motion.div>
      </section>

      <Separator />

      {/* Testimonials Section */}
      <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <h2 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
            Loved by Teams
          </h2>
          <p className="text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto">
            See what our users have to say
          </p>
        </motion.div>

        <motion.div
          className="grid md:grid-cols-3 gap-8"
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          {testimonials.map(({ name, role, quote, initial }) => (
            <motion.div key={name} variants={itemVariants}>
              <Card className="surface-panel rounded-[1.75rem]">
                <CardContent className="pt-6">
                  <p className="mb-6 italic text-muted-foreground">
                    &quot;{quote}&quot;
                  </p>
                  <div className="flex items-center gap-3">
                    <Avatar fallback={initial} />
                    <div>
                      <p className="font-semibold text-slate-900 dark:text-white">
                        {name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {role}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </section>

      <Separator />

      <section className="mx-auto max-w-5xl px-4 py-20 sm:px-6 lg:px-8">
        <motion.div
          className="mb-14 text-center"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <Badge variant="outline" className="mb-4 border-primary/20 bg-primary/5 px-4 py-1 text-primary">
            FAQ
          </Badge>
          <h2 className="text-4xl font-bold text-foreground">Questions teams ask before they adopt it</h2>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-muted-foreground">
            A richer accordion-based section gives the landing page a stronger product narrative and makes the UI feel more complete.
          </p>
        </motion.div>

        <Accordion type="single" collapsible className="grid gap-4">
          {faqs.map((faq, index) => (
            <AccordionItem key={faq.question} value={`faq-${index}`}>
              <AccordionTrigger>{faq.question}</AccordionTrigger>
              <AccordionContent>{faq.answer}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </section>

      <Separator />

      <MarketingFooter />
    </div>
  )
}
