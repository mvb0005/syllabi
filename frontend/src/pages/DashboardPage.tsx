import { useEffect, useState } from 'react'
import { getHealth, type HealthResponse } from '@/api/client'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export function DashboardPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : 'Unknown error'),
      )
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">
          Welcome to the AI-powered Learning Management System.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">API Status</CardTitle>
            <CardDescription>Backend health check</CardDescription>
          </CardHeader>
          <CardContent>
            {health ? (
              <Badge variant="default">
                {health.status}
              </Badge>
            ) : error ? (
              <Badge variant="destructive">offline</Badge>
            ) : (
              <span className="text-sm text-muted-foreground">checking…</span>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Courses</CardTitle>
            <CardDescription>Active learning paths</CardDescription>
          </CardHeader>
          <CardContent>
            <span className="text-3xl font-bold">—</span>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Pending Grades</CardTitle>
            <CardDescription>Awaiting AI review</CardDescription>
          </CardHeader>
          <CardContent>
            <span className="text-3xl font-bold">—</span>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
