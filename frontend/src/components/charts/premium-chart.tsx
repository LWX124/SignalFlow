'use client'

import { useEffect, useRef, memo } from 'react'
import { createChart, IChartApi, ColorType } from 'lightweight-charts'
import { useTheme } from 'next-themes'

interface PremiumChartProps {
  data: {
    time: string
    premium: number
  }[]
  threshold?: { high: number; low: number }
  height?: number
  className?: string
}

export const PremiumChart = memo(function PremiumChart({
  data,
  threshold = { high: 5, low: -3 },
  height = 200,
  className,
}: PremiumChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const { theme } = useTheme()

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return

    const isDark = theme === 'dark'

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height,
      layout: {
        background: {
          type: ColorType.Solid,
          color: isDark ? '#1a1a1a' : '#ffffff',
        },
        textColor: isDark ? '#d1d5db' : '#374151',
      },
      rightPriceScale: {
        borderVisible: false,
      },
      timeScale: {
        borderVisible: false,
      },
      grid: {
        vertLines: { visible: false },
        horzLines: { color: isDark ? '#374151' : '#e5e7eb' },
      },
    })

    chartRef.current = chart

    // Premium area series
    const premiumSeries = chart.addAreaSeries({
      topColor: 'rgba(59, 130, 246, 0.4)',
      bottomColor: 'rgba(59, 130, 246, 0.0)',
      lineColor: '#3b82f6',
      lineWidth: 2,
    })

    premiumSeries.setData(
      data.map((d) => ({ time: d.time as unknown as number, value: d.premium }))
    )

    // High threshold line
    const highLine = chart.addLineSeries({
      color: '#ef4444',
      lineWidth: 1,
      lineStyle: 2, // Dashed
    })

    highLine.setData(
      data.map((d) => ({ time: d.time as unknown as number, value: threshold.high }))
    )

    // Low threshold line
    const lowLine = chart.addLineSeries({
      color: '#22c55e',
      lineWidth: 1,
      lineStyle: 2,
    })

    lowLine.setData(
      data.map((d) => ({ time: d.time as unknown as number, value: threshold.low }))
    )

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth })
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [data, threshold, height, theme])

  return <div ref={containerRef} className={className} />
})
