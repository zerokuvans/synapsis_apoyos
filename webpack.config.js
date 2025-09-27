const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const TerserPlugin = require('terser-webpack-plugin');
const CompressionPlugin = require('compression-webpack-plugin');
const BrotliPlugin = require('brotli-webpack-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const WebpackManifestPlugin = require('webpack-manifest-plugin');
const ImageMinimizerPlugin = require('image-minimizer-webpack-plugin');

const isProduction = process.env.NODE_ENV === 'production';

module.exports = {
  mode: isProduction ? 'production' : 'development',
  
  entry: {
    // Archivos principales
    main: './app/static/src/js/main.js',
    admin: './app/static/src/js/admin.js',
    dashboard: './app/static/src/js/dashboard.js',
    
    // Estilos
    styles: './app/static/src/css/main.css',
    admin_styles: './app/static/src/css/admin.css',
  },
  
  output: {
    path: path.resolve(__dirname, 'app/static/dist'),
    filename: isProduction ? 'js/[name].[contenthash:8].js' : 'js/[name].js',
    chunkFilename: isProduction ? 'js/[name].[contenthash:8].chunk.js' : 'js/[name].chunk.js',
    publicPath: '/static/dist/',
    clean: true,
  },
  
  module: {
    rules: [
      // JavaScript
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
              ['@babel/preset-env', {
                targets: {
                  browsers: ['> 1%', 'last 2 versions', 'not ie <= 8']
                },
                useBuiltIns: 'usage',
                corejs: 3
              }]
            ],
            plugins: [
              '@babel/plugin-syntax-dynamic-import',
              '@babel/plugin-proposal-class-properties'
            ]
          }
        }
      },
      
      // CSS
      {
        test: /\.css$/,
        use: [
          isProduction ? MiniCssExtractPlugin.loader : 'style-loader',
          {
            loader: 'css-loader',
            options: {
              importLoaders: 1,
              sourceMap: !isProduction
            }
          },
          {
            loader: 'postcss-loader',
            options: {
              postcssOptions: {
                plugins: [
                  ['autoprefixer'],
                  ...(isProduction ? [['cssnano', { preset: 'default' }]] : [])
                ]
              }
            }
          }
        ]
      },
      
      // SCSS/Sass
      {
        test: /\.s[ac]ss$/,
        use: [
          isProduction ? MiniCssExtractPlugin.loader : 'style-loader',
          {
            loader: 'css-loader',
            options: {
              importLoaders: 2,
              sourceMap: !isProduction
            }
          },
          {
            loader: 'postcss-loader',
            options: {
              postcssOptions: {
                plugins: [
                  ['autoprefixer'],
                  ...(isProduction ? [['cssnano', { preset: 'default' }]] : [])
                ]
              }
            }
          },
          {
            loader: 'sass-loader',
            options: {
              sourceMap: !isProduction
            }
          }
        ]
      },
      
      // Imágenes
      {
        test: /\.(png|jpe?g|gif|svg|webp)$/i,
        type: 'asset',
        parser: {
          dataUrlCondition: {
            maxSize: 8 * 1024 // 8kb
          }
        },
        generator: {
          filename: 'images/[name].[contenthash:8][ext]'
        }
      },
      
      // Fuentes
      {
        test: /\.(woff|woff2|eot|ttf|otf)$/i,
        type: 'asset/resource',
        generator: {
          filename: 'fonts/[name].[contenthash:8][ext]'
        }
      },
      
      // Otros archivos
      {
        test: /\.(pdf|doc|docx|xls|xlsx)$/i,
        type: 'asset/resource',
        generator: {
          filename: 'files/[name].[contenthash:8][ext]'
        }
      }
    ]
  },
  
  plugins: [
    // Limpiar directorio de salida
    new CleanWebpackPlugin(),
    
    // Extraer CSS en archivos separados
    ...(isProduction ? [
      new MiniCssExtractPlugin({
        filename: 'css/[name].[contenthash:8].css',
        chunkFilename: 'css/[name].[contenthash:8].chunk.css'
      })
    ] : []),
    
    // Generar manifest para mapeo de archivos
    new WebpackManifestPlugin.WebpackManifestPlugin({
      fileName: 'manifest.json',
      publicPath: '/static/dist/',
      writeToFileEmit: true
    }),
    
    // Compresión gzip
    ...(isProduction ? [
      new CompressionPlugin({
        filename: '[path][base].gz',
        algorithm: 'gzip',
        test: /\.(js|css|html|svg)$/,
        threshold: 8192,
        minRatio: 0.8,
        compressionOptions: {
          level: 9
        }
      })
    ] : []),
    
    // Compresión Brotli
    ...(isProduction ? [
      new BrotliPlugin({
        asset: '[path].br[query]',
        test: /\.(js|css|html|svg)$/,
        threshold: 8192,
        minRatio: 0.8,
        quality: 11
      })
    ] : [])
  ],
  
  optimization: {
    minimize: isProduction,
    minimizer: [
      // Minificar JavaScript
      new TerserPlugin({
        terserOptions: {
          compress: {
            drop_console: isProduction,
            drop_debugger: isProduction,
            pure_funcs: isProduction ? ['console.log', 'console.info'] : []
          },
          mangle: {
            safari10: true
          },
          format: {
            comments: false
          }
        },
        extractComments: false
      }),
      
      // Minificar CSS
      new CssMinimizerPlugin({
        minimizerOptions: {
          preset: [
            'default',
            {
              discardComments: { removeAll: true }
            }
          ]
        }
      }),
      
      // Optimizar imágenes
      ...(isProduction ? [
        new ImageMinimizerPlugin({
          minimizer: {
            implementation: ImageMinimizerPlugin.imageminMinify,
            options: {
              plugins: [
                ['imagemin-mozjpeg', { quality: 85, progressive: true }],
                ['imagemin-pngquant', { quality: [0.6, 0.8] }],
                ['imagemin-svgo', {
                  plugins: [
                    {
                      name: 'preset-default',
                      params: {
                        overrides: {
                          removeViewBox: false
                        }
                      }
                    }
                  ]
                }],
                ['imagemin-gifsicle', { optimizationLevel: 3 }]
              ]
            }
          },
          generator: [
            // Generar WebP
            {
              type: 'asset',
              preset: 'webp-custom-name',
              implementation: ImageMinimizerPlugin.imageminGenerate,
              options: {
                plugins: ['imagemin-webp']
              }
            }
          ]
        })
      ] : [])
    ],
    
    // Dividir código en chunks
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        // Vendor libraries
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
          priority: 10
        },
        
        // Código común
        common: {
          name: 'common',
          minChunks: 2,
          chunks: 'all',
          priority: 5,
          reuseExistingChunk: true
        },
        
        // CSS común
        styles: {
          name: 'styles',
          test: /\.css$/,
          chunks: 'all',
          enforce: true
        }
      }
    },
    
    // Runtime chunk separado
    runtimeChunk: {
      name: 'runtime'
    }
  },
  
  resolve: {
    extensions: ['.js', '.jsx', '.ts', '.tsx', '.css', '.scss'],
    alias: {
      '@': path.resolve(__dirname, 'app/static/src'),
      '@js': path.resolve(__dirname, 'app/static/src/js'),
      '@css': path.resolve(__dirname, 'app/static/src/css'),
      '@images': path.resolve(__dirname, 'app/static/src/images'),
      '@fonts': path.resolve(__dirname, 'app/static/src/fonts')
    }
  },
  
  devtool: isProduction ? 'source-map' : 'eval-source-map',
  
  performance: {
    hints: isProduction ? 'warning' : false,
    maxEntrypointSize: 250000,
    maxAssetSize: 250000
  },
  
  stats: {
    colors: true,
    modules: false,
    children: false,
    chunks: false,
    chunkModules: false
  }
};

// Configuración específica para desarrollo
if (!isProduction) {
  module.exports.devServer = {
    contentBase: path.join(__dirname, 'app/static'),
    compress: true,
    port: 3000,
    hot: true,
    overlay: true,
    stats: 'minimal'
  };
}