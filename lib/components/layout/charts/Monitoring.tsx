import React, { PureComponent } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const data = [
  {
    name: "Time A",
    CPU: 4000,
    RAM: 2400,
    HDD: 2400,
  },
  {
    name: "Time B",
    CPU: 3000,
    RAM: 1398,
    HDD: 2210,
  },
  {
    name: "Time C",
    CPU: 2000,
    RAM: 9800,
    HDD: 2290,
  },
  {
    name: "Time D",
    CPU: 2780,
    RAM: 3908,
    HDD: 2000,
  },
  {
    name: "Time E",
    CPU: 1890,
    RAM: 4800,
    HDD: 2181,
  },
  {
    name: "Time F",
    CPU: 2390,
    RAM: 3800,
    HDD: 2500,
  },
  {
    name: "Time G",
    CPU: 3490,
    RAM: 4300,
    HDD: 2100,
  },
];

export default class MonitorGraph extends PureComponent {
  static jsfiddleUrl = "https://jsfiddle.net/alidingling/xqjtetw0/";

  render() {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorHDD" x1="0" y1="0" x2="0" y2="1">
              <stop offset="15%" stopColor="#D62F0B" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#D62F0B" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorUv" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#8884d8" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorPv" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#82ca9d" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#82ca9d" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="name" />
          <YAxis />
          <CartesianGrid strokeDasharray="3 3" />
          <Tooltip />
          <Area type="monotone" dataKey="HDD" stroke="#000" fillOpacity={1} fill="url(#colorHDD)" />
          <Area
            type="monotone"
            dataKey="CPU"
            stroke="#8884d8"
            fillOpacity={1}
            fill="url(#colorUv)"
          />
          <Area
            type="monotone"
            dataKey="RAM"
            stroke="#82ca9d"
            fillOpacity={1}
            fill="url(#colorPv)"
          />
          <Legend verticalAlign="top" height={36} />
          <Line name="pv of pages" type="monotone" dataKey="CPU" stroke="#8884d8" />
          <Line name="uv of pages" type="monotone" dataKey="RAM" stroke="#82ca9d" />
        </AreaChart>
      </ResponsiveContainer>
    );
  }
}
