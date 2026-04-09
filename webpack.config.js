/**
 * Webpack 配置 - TypeScript 构建配置
 */

const path = require('path');

module.exports = (env, argv) => {
  const isProduction = argv.mode === 'production';

  return {
    mode: isProduction ? 'production' : 'development',
    entry: {
      app: './web/ui/js/app.ts',
      tools: './web/ui/js/tools.ts',
      sessions: './web/ui/js/sessions.ts',
      settings: './web/ui/js/settings.ts',
      client: './web/ui/js/client.ts'
    },
    output: {
      filename: '[name].bundle.js',
      path: path.resolve(__dirname, 'web/ui/dist'),
      clean: true
    },
    resolve: {
      extensions: ['.ts', '.tsx', '.js', '.jsx'],
      alias: {
        '@': path.resolve(__dirname, 'web/ui/js')
      }
    },
    module: {
      rules: [
        {
          test: /\.tsx?$/,
          use: 'ts-loader',
          exclude: /node_modules/
        }
      ]
    },
    devtool: isProduction ? 'source-map' : 'eval-source-map',
    optimization: {
      splitChunks: {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
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
      },
      minimize: isProduction
    },
    performance: {
      hints: 'warning',
      maxAssetSize: 244 * 1024,
      maxEntrypointSize: 244 * 1024
    }
  };
};
