import * as React from "react"
import { ChevronLeft, ChevronRight, MoreHorizontal } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "./button"

interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
  className?: string
}

export function Pagination({
  currentPage,
  totalPages,
  onPageChange,
  className,
}: PaginationProps) {
  const renderPageNumbers = () => {
    const pages = []
    const showEllipsisStart = currentPage > 3
    const showEllipsisEnd = currentPage < totalPages - 2

    // 始终显示第一页
    pages.push(
      <Button
        key={1}
        variant={currentPage === 1 ? "primary" : "ghost"}
        size="sm"
        onClick={() => onPageChange(1)}
      >
        1
      </Button>
    )

    // 开始省略号
    if (showEllipsisStart) {
      pages.push(
        <span key="ellipsis-start" className="px-2">
          <MoreHorizontal className="h-4 w-4" />
        </span>
      )
    }

    // 中间页码
    const start = Math.max(2, currentPage - 1)
    const end = Math.min(totalPages - 1, currentPage + 1)

    for (let i = start; i <= end; i++) {
      pages.push(
        <Button
          key={i}
          variant={currentPage === i ? "primary" : "ghost"}
          size="sm"
          onClick={() => onPageChange(i)}
        >
          {i}
        </Button>
      )
    }

    // 结束省略号
    if (showEllipsisEnd) {
      pages.push(
        <span key="ellipsis-end" className="px-2">
          <MoreHorizontal className="h-4 w-4" />
        </span>
      )
    }

    // 始终显示最后一页
    if (totalPages > 1) {
      pages.push(
        <Button
          key={totalPages}
          variant={currentPage === totalPages ? "primary" : "ghost"}
          size="sm"
          onClick={() => onPageChange(totalPages)}
        >
          {totalPages}
        </Button>
      )
    }

    return pages
  }

  if (totalPages <= 1) return null

  return (
    <div className={cn("flex items-center justify-center gap-2", className)}>
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
      >
        <ChevronLeft className="h-4 w-4" />
      </Button>

      {renderPageNumbers()}

      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
      >
        <ChevronRight className="h-4 w-4" />
      </Button>
    </div>
  )
}
