import {
  Card,
  Typography,
  Row,
  Col,
  Statistic,
  Spin,
  Alert,
  Divider,
} from 'antd'
import { BarChartOutlined, FileTextOutlined, FireOutlined, TrophyOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { longhubangApi } from '@/services/longhubangApi'

const { Title, Paragraph } = Typography

export default function LonghubangStatistics() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['longhubangStatistics'],
    queryFn: longhubangApi.getStatistics,
  })

  return (
    <div style={{ width: '100%' }}>
      <Card>
        <Title level={2}><BarChartOutlined /> 数据统计</Title>
        <Paragraph>
          智瞰龙虎模块数据统计概览
        </Paragraph>
      </Card>

      {isError && (
        <Alert
          message="获取统计数据失败"
          description={(error as Error)?.message || '请稍后重试'}
          type="error"
          showIcon
        />
      )}

      <Spin spinning={isLoading}>
        <Row gutter={16} style={{ marginTop: 16 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总报告数"
                value={data?.total_reports || 0}
                prefix={<FileTextOutlined />}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="总分析股票数"
                value={data?.total_stocks || 0}
                prefix={<FireOutlined />}
                valueStyle={{ color: '#cf1322' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="总游资数"
                value={data?.total_youzi || 0}
                prefix={<TrophyOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="总推荐股票数"
                value={data?.total_recommended || 0}
                prefix={<BarChartOutlined />}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>

        {data && Object.keys(data).length > 0 && (
          <>
            <Divider />
            <Card title="详细统计">
              <Row gutter={16}>
                {Object.entries(data).map(([key, value]) => {
                  if (['total_reports', 'total_stocks', 'total_youzi', 'total_recommended'].includes(key)) {
                    return null
                  }
                  return (
                    <Col span={8} key={key} style={{ marginBottom: 16 }}>
                      <Card size="small">
                        <Statistic
                          title={key.replace(/_/g, ' ')}
                          value={typeof value === 'number' ? value : 0}
                        />
                      </Card>
                    </Col>
                  )
                })}
              </Row>
            </Card>
          </>
        )}
      </Spin>
    </div>
  )
}
