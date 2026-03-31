import { Typography } from 'antd'

const { Title, Paragraph, Text } = Typography

export default function Home() {
  return (
    <div>
      <Title level={2}>欢迎使用 AI Agents Stock</Title>
      <Paragraph>
        复合多AI智能体股票团队分析系统
      </Paragraph>
      <div style={{ marginTop: '20px' }}>
        <Title level={4}>系统状态</Title>
        <Text strong>前端运行正常</Text>
      </div>
      <div style={{ marginTop: '20px' }}>
        <Title level={4}>快速开始</Title>
        <ul>
          <li>后端：FastAPI 运行在 http://localhost:8000</li>
          <li>前端：React 运行在 http://localhost:5173</li>
          <li>API 文档：访问 http://localhost:8000/docs</li>
        </ul>
      </div>
    </div>
  )
}
