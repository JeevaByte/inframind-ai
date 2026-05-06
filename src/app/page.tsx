"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Avatar } from "@/components/ui/avatar"
import {
  BarChart3,
  Shield,
  TrendingDown,
  Eye,
  Upload,
  FileText,
  ArrowRight,
} from "lucide-react"
import Link from "next/link"
import { motion } from "framer-motion"

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
    quote: "InfraMind AI helped us identify $50k/month in unnecessary infrastructure costs.",
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
    <div className="min-h-screen bg-white dark:bg-slate-950">
      {/* Hero Section */}
      <section className="relative mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 overflow-hidden">
        <div className="absolute -top-40 -right-40 h-80 w-80 rounded-full bg-blue-500/10 blur-3xl dark:bg-blue-500/5" />
        <div className="absolute -bottom-40 -left-40 h-80 w-80 rounded-full bg-purple-500/10 blur-3xl dark:bg-purple-500/5" />

        <motion.div
          className="relative space-y-6 text-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <h1 className="text-5xl sm:text-6xl font-bold text-slate-900 dark:text-white">
            InfraMind AI
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto">
            AI-powered infrastructure analysis for Terraform, CloudFormation, and Kubernetes. Identify security risks, optimize costs, and improve best practices.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-8">
            <Link href="/upload">
              <Button size="lg" className="gap-2">
                Get Started <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Button size="lg" variant="outline">
              View Demo
            </Button>
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
              <Card className="h-full hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start gap-4">
                    <div className="p-2 bg-blue-100 dark:bg-blue-950 rounded-lg">
                      <Icon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                    </div>
                    <CardTitle className="text-xl">{title}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-slate-600 dark:text-slate-300">
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
                <Card className="h-full">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-2">
                          {number}
                        </div>
                        <CardTitle>{title}</CardTitle>
                      </div>
                      <Icon className="h-8 w-8 text-slate-400" />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-slate-600 dark:text-slate-300">
                      {description}
                    </p>
                  </CardContent>
                </Card>
                {index < steps.length - 1 && (
                  <div className="hidden md:block absolute top-1/2 -right-4 transform -translate-y-1/2">
                    <ArrowRight className="h-8 w-8 text-slate-300 dark:text-slate-700" />
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
              <Card>
                <CardContent className="pt-6">
                  <p className="text-slate-600 dark:text-slate-300 italic mb-6">
                    &quot;{quote}&quot;
                  </p>
                  <div className="flex items-center gap-3">
                    <Avatar fallback={initial} />
                    <div>
                      <p className="font-semibold text-slate-900 dark:text-white">
                        {name}
                      </p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
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

      {/* Footer */}
      <footer className="bg-slate-50 dark:bg-slate-900 py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <h3 className="font-bold text-slate-900 dark:text-white mb-4">
                InfraMind AI
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                AI-powered infrastructure analysis for DevOps and Cloud teams.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-slate-900 dark:text-white mb-4">
                Product
              </h4>
              <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
                <li>
                  <Link href="#" className="hover:text-slate-900 dark:hover:text-white">
                    Features
                  </Link>
                </li>
                <li>
                  <Link href="#" className="hover:text-slate-900 dark:hover:text-white">
                    Pricing
                  </Link>
                </li>
                <li>
                  <Link href="#" className="hover:text-slate-900 dark:hover:text-white">
                    Documentation
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-slate-900 dark:text-white mb-4">
                Company
              </h4>
              <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
                <li>
                  <Link href="#" className="hover:text-slate-900 dark:hover:text-white">
                    About
                  </Link>
                </li>
                <li>
                  <Link href="#" className="hover:text-slate-900 dark:hover:text-white">
                    Blog
                  </Link>
                </li>
                <li>
                  <Link href="#" className="hover:text-slate-900 dark:hover:text-white">
                    Contact
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-slate-900 dark:text-white mb-4">
                Legal
              </h4>
              <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
                <li>
                  <Link href="#" className="hover:text-slate-900 dark:hover:text-white">
                    Privacy
                  </Link>
                </li>
                <li>
                  <Link href="#" className="hover:text-slate-900 dark:hover:text-white">
                    Terms
                  </Link>
                </li>
              </ul>
            </div>
          </div>

          <Separator />

          <div className="mt-8 pt-8 text-center text-sm text-slate-600 dark:text-slate-400">
            <p>&copy; {new Date().getFullYear()} InfraMind AI. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
