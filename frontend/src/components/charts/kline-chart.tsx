'use client'

import { useEffect, useRef, memo } from 'react'
import {
  createChart,
  IChartApi,
  ColorType,
} from 'lightweight-charts'
import { useTheme } from 'next-themes'

interface KLineChartProps {
  data: {
    time: string
    open: number
    high: number
    low: number
    close: number
    volume?: number
  }[]
  height?: number
  className?: string
}

export const KLineChart = memo(function KLineChart({
  data,
  height = 400,
  className,
}: KLineChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const { theme } = useTheme()

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return

    const isDark = theme === 'dark'

    // Create chart
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
      grid: {
        vertLines: { color: isDark ? '#374151' : '#e5e7eb' },
        horzLines: { color: isDark ? '#374151' : '#e5e7eb' },
      },
      rightPriceScale: {
        borderColor: isDark ? '#374151' : '#e5e7eb',
      },
      timeScale: {
        borderColor: isDark ? '#374151' : '#e5e7eb',
        timeVisible: true,
      },
      crosshair: {
        mode: 0,
      },
    })

    chartRef.current = chart

    // Add candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderDownColor: '#ef4444',
      borderUpColor: '#22c55e',
      wickDownColor: '#ef4444',
      wickUpColor: '#22c55e',
    })

    candlestickSeries.setData(
      data.map((d) => ({
        time: d.time as unknown as number,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
      }))
    )

    // Add volume series if data has volume
    if (data.some((d) => d.volume !== undefined)) {
      const volumeSeries = chart.addHistogramSeries({
        priceFormat: { type: 'volume' },
        priceScaleId: '',
      })

      volumeSeries.priceScale().applyOptions({
        scaleMargins: { top: 0.8, bottom: 0 },
      })

      volumeSeries.setData(
        data.map((d) => ({
          time: d.time as unknown as number,
          value: d.volume ?? 0,
          color: d.close >= d.open ? '#22c55e80' : '#ef444480',
        }))
      )
    }

    // Auto resize
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
  }, [data, height, theme])

  return <div ref={containerRef} className={className} />
})
