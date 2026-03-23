/**
 * Webpack 配置 - 代码分割
 */

const path = require('path');

module.exports = {
  entry: {
    app: './app.js',
    tools: './tools.js',
    sessions: './sessions.js',
    settings: './settings.js',
    client: './client.js'
  },
  output: {
    filename: '[name].bundle.js',
    path: path.resolve(__dirname, '../dist'),
    clean: true
  },
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\/]node_modules[\/]/,
          name: 'vendors',
          priority: 10
        },
        common: {
          name: 'common',
          minChunks: 2,
          priority: 5,
          reuseExistingChunk: true
        }
      }
    }
  },
  performance: {
    hints: 'warning',
    maxAssetSize: 244 * 1024,
    maxEntrypointSize: 244 * 1024
  }
};
