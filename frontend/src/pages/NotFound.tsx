import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { FileQuestion, Home, ArrowLeft } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/10 via-background to-secondary/10 p-4">
      <Card className="w-full max-w-md animate-scale-in">
        <CardContent className="pt-6">
          <div className="text-center space-y-6">
            {/* Icon */}
            <div className="flex justify-center">
              <div className="h-24 w-24 rounded-full bg-primary/10 flex items-center justify-center">
                <FileQuestion className="h-12 w-12 text-primary" />
              </div>
            </div>

            {/* Text */}
            <div className="space-y-2">
              <h1 className="text-4xl font-bold text-text-primary">404</h1>
              <p className="text-xl font-semibold text-text-primary">页面未找到</p>
              <p className="text-sm text-text-secondary">
                抱歉，您访问的页面不存在或已被移除。
              </p>
            </div>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button onClick={() => window.history.back()} variant="outline">
                <ArrowLeft className="h-4 w-4 mr-2" />
                返回上一页
              </Button>
              <Link to="/dashboard">
                <Button>
                  <Home className="h-4 w-4 mr-2" />
                  回到首页
                </Button>
              </Link>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
