import { useEffect } from 'react'
import { Card, Typography, Form, Switch, InputNumber, Button, message, Skeleton, Space } from 'antd'
import { SaveOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { monitorApi } from '@/services/monitorApi'
import type { MonitorConfig } from '@/types/monitor'

const { Title, Paragraph } = Typography

export default function MonitorConfig() {
  const [form] = Form.useForm<MonitorConfig>()
  const queryClient = useQueryClient()

  const { data: configData, isLoading } = useQuery({
    queryKey: ['monitorConfig'],
    queryFn: monitorApi.getConfig,
  })

  useEffect(() => {
    if (configData?.config) {
      form.setFieldsValue(configData.config)
    }
  }, [configData, form])

  const mutation = useMutation({
    mutationFn: (values: MonitorConfig) => monitorApi.updateConfig(values),
    onSuccess: () => {
      message.success('监控配置已更新')
      queryClient.invalidateQueries({ queryKey: ['monitorConfig'] })
    },
    onError: (error: any) => {
      message.error(`更新失败: ${error.message || '未知错误'}`)
    },
  })

  const onFinish = (values: MonitorConfig) => {
    mutation.mutate(values)
  }

  if (isLoading) {
    return <Skeleton active />
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Title level={2}>盯盘配置</Title>
        <Paragraph>
          配置智能盯盘系统的全局参数。
        </Paragraph>
      </Card>

      <Card title="系统配置" style={{ maxWidth: 800 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          initialValues={{
            monitor_enabled: false,
            check_interval: 300,
            auto_notification: true,
          }}
        >
          <Form.Item
            name="monitor_enabled"
            label="启用智能盯盘"
            valuePropName="checked"
            extra="开启后，系统将自动按设定的频率检查监测列表中的股票状态。"
          >
            <Switch checkedChildren="开启" unCheckedChildren="关闭" />
          </Form.Item>

          <Form.Item
            name="check_interval"
            label="全局检查间隔（秒）"
            rules={[{ required: true, message: '请输入检查间隔' }]}
            extra="系统执行轮询检查的默认时间间隔，个股可单独覆盖此设置。"
          >
            <InputNumber min={10} max={3600} style={{ width: 200 }} />
          </Form.Item>

          <Form.Item
            name="auto_notification"
            label="自动发送通知"
            valuePropName="checked"
            extra="开启后，当股票价格触发设定的条件时，系统会自动发送提醒通知。"
          >
            <Switch checkedChildren="开启" unCheckedChildren="关闭" />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              icon={<SaveOutlined />}
              loading={mutation.isPending}
            >
              保存配置
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </Space>
  )
}
