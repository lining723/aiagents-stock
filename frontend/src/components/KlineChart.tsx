import React from 'react'
import ReactECharts from 'echarts-for-react'
import type { KlineData } from '@/types/stock'

interface Props {
  data: KlineData[]
  title?: string
}

export default function KlineChart({ data, title = 'K线走势图' }: Props) {
  if (!data || data.length === 0) {
    return <div style={{ textAlign: 'center', padding: '50px 0', color: '#999' }}>暂无K线数据</div>
  }

  // 提取类目轴数据
  const categoryData = data.map(item => item.date)
  
  // 提取K线数据: [开盘, 收盘, 最低, 最高]
  const values = data.map(item => [item.open, item.close, item.low, item.high])
  
  // 提取均线数据
  const ma5 = data.map(item => item.ma5 || null)
  const ma10 = data.map(item => item.ma10 || null)
  const ma20 = data.map(item => item.ma20 || null)
  
  // 提取成交量数据: [索引, 成交量, 涨跌标识(1涨 -1跌)]
  const volumes = data.map((item, index) => [
    index,
    item.volume,
    item.close >= item.open ? 1 : -1
  ])

  const upColor = '#ef232a'
  const upBorderColor = '#8A0000'
  const downColor = '#14b143'
  const downBorderColor = '#008F28'

  const option = {
    title: {
      text: title,
      left: 0
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      borderWidth: 1,
      borderColor: '#ccc',
      padding: 10,
      textStyle: {
        color: '#000'
      }
    },
    legend: {
      data: ['日K', 'MA5', 'MA10', 'MA20'],
      top: 0,
      right: '10%'
    },
    grid: [
      {
        left: '5%',
        right: '5%',
        height: '55%'
      },
      {
        left: '5%',
        right: '5%',
        top: '75%',
        height: '15%'
      }
    ],
    xAxis: [
      {
        type: 'category',
        data: categoryData,
        boundaryGap: false,
        axisLine: { onZero: false },
        splitLine: { show: false },
        min: 'dataMin',
        max: 'dataMax'
      },
      {
        type: 'category',
        gridIndex: 1,
        data: categoryData,
        boundaryGap: false,
        axisLine: { onZero: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        min: 'dataMin',
        max: 'dataMax'
      }
    ],
    yAxis: [
      {
        scale: true,
        splitArea: { show: false },
        splitLine: {
          lineStyle: {
            color: '#eee',
            type: 'dashed'
          }
        }
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 0,
        end: 100
      },
      {
        show: true,
        xAxisIndex: [0, 1],
        type: 'slider',
        bottom: '2%',
        start: 0,
        end: 100
      }
    ],
    series: [
      {
        name: '日K',
        type: 'candlestick',
        data: values,
        itemStyle: {
          color: upColor,
          color0: downColor,
          borderColor: upBorderColor,
          borderColor0: downBorderColor
        }
      },
      {
        name: 'MA5',
        type: 'line',
        data: ma5,
        smooth: true,
        lineStyle: { opacity: 0.5 },
        symbol: 'none'
      },
      {
        name: 'MA10',
        type: 'line',
        data: ma10,
        smooth: true,
        lineStyle: { opacity: 0.5 },
        symbol: 'none'
      },
      {
        name: 'MA20',
        type: 'line',
        data: ma20,
        smooth: true,
        lineStyle: { opacity: 0.5 },
        symbol: 'none'
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes,
        itemStyle: {
          color: function(params: any) {
            return params.data[2] === 1 ? upColor : downColor
          }
        }
      }
    ]
  }

  return (
    <ReactECharts
      option={option}
      style={{ height: 500, width: '100%' }}
      opts={{ renderer: 'canvas' }}
    />
  )
}