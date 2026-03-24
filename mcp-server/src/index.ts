#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

class MCPServer {
  private server: Server;

  constructor() {
    this.server = new Server(
      {
        name: "zhineng-bridge-mcp",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupHandlers();
  }

  private setupHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: "hello_world",
            description: "A simple hello world tool to test MCP server",
            inputSchema: {
              type: "object",
              properties: {
                name: {
                  type: "string",
                  description: "Name to greet",
                },
              },
              required: ["name"],
            },
          },
        ],
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      if (name === "hello_world") {
        const greetName = (args as { name: string }).name;
        return {
          content: [
            {
              type: "text",
              text: `Hello, ${greetName}! zhineng-bridge MCP server is running!`,
            },
          ],
        };
      }

      throw new Error(`Unknown tool: ${name}`);
    });
  }

  async start() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("zhineng-bridge MCP server running on stdio");
  }
}

const server = new MCPServer();
server.start().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
