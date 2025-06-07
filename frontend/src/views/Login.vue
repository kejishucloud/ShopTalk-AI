<template>
  <div class="login-container">
    <!-- 智能背景动画 -->
    <div class="ai-background">
      <!-- 毛玻璃背景容器 -->
      <div class="glassmorphism-container">
        <div class="absolute inset-0 bg-black/20 backdrop-blur-xl rounded-2xl border border-white/10 shadow-2xl"></div>
      </div>
      
      <!-- SVG定义 -->
      <svg width="0" height="0" style="position: absolute;">
        <defs>
          <clipPath id="squircleClip" clipPathUnits="objectBoundingBox">
            <path d="M 0,0.5 C 0,0 0,0 0.5,0 S 1,0 1,0.5 1,1 0.5,1 0,1 0,0.5"></path>
          </clipPath>
        </defs>
      </svg>
      
      <!-- AI节点网络 -->
      <div class="network-nodes">
        <!-- 电商平台节点组 - 左侧 -->
        <div class="node-group ecommerce-nodes">
          <div class="platform-section">
            <!-- 国内电商平台 -->
            <div class="domestic-platforms">
              <div class="section-label">国内电商</div>
              <div class="platform-node taobao" data-platform="淘宝">
                <div class="modern-platform-icon taobao-modern">
                  <svg viewBox="0 0 24 24" fill="currentColor" class="platform-svg">
                    <text x="12" y="16" text-anchor="middle" class="platform-text">淘宝</text>
                  </svg>
                </div>
                <div class="platform-name">淘宝</div>
              </div>
              <div class="platform-node jd" data-platform="京东">
                <div class="modern-platform-icon jd-modern">
                  <svg viewBox="0 0 24 24" fill="currentColor" class="platform-svg">
                    <text x="12" y="16" text-anchor="middle" class="platform-text">京东</text>
                  </svg>
                </div>
                <div class="platform-name">京东</div>
              </div>
              <div class="platform-node pdd" data-platform="拼多多">
                <div class="modern-platform-icon pdd-modern">
                  <svg viewBox="0 0 24 24" fill="currentColor" class="platform-svg">
                    <circle cx="8" cy="8" r="3" fill="currentColor"/>
                    <circle cx="16" cy="8" r="3" fill="currentColor"/>
                    <circle cx="12" cy="16" r="3" fill="currentColor"/>
                  </svg>
                </div>
                <div class="platform-name">拼多多</div>
              </div>
            </div>
            
            <!-- 国外电商平台 -->
            <div class="international-platforms">
              <div class="section-label">国外电商</div>
              <div class="platform-node amazon" data-platform="Amazon">
                <div class="modern-platform-icon amazon-modern">
                  <svg viewBox="0 0 24 24" fill="currentColor" class="platform-svg">
                    <path d="M15.7 14.5c-1.7 1.3-4.3 1.9-6.5 1.9-3.1 0-5.8-1.1-7.9-3-.2-.2 0-.4.2-.3 2.4 1.4 5.4 2.2 8.4 2.2 2.1 0 4.3-.4 6.4-1.3.3-.1.6.2.3.5z"/>
                    <path d="M16.5 13.6c-.2-.3-1.4-.1-2 0-.2 0-.2-.1 0-.2 1-.7 2.6-.5 2.8-.3.2.3-.5 2.2-2.8 3.1-.2.1-.4 0-.3-.2.3-.8 1-1.9.8-2.3z"/>
                    <path d="M14.4 8.9v-.7c0-.1.1-.2.2-.2h3.6c.1 0 .2.1.2.2v.6c0 .1-.1.2-.2.3l-1.9 2.6c.7 0 1.4.1 2 .4.1 0 .1.2 0 .3l-.8 1.1c-.1.1-.2.1-.3 0-1-.5-2.3-.6-3.4 0-.1.1-.3 0-.3-.1l-.8-1.1c-.1-.1 0-.3.1-.3.8-.5 1.8-.6 2.8-.3l2-2.7c.1-.1.1-.2.1-.3h-3.1c-.1 0-.2-.1-.2-.2z"/>
                    <path d="M5.8 13h-1.1c-.1 0-.2-.1-.2-.2V7.5c0-.1.1-.2.2-.2h1c.1 0 .2.1.2.2v.7h.1c.3-.7.8-1 1.5-1 .7 0 1.1.3 1.4 1 .3-.7.9-1 1.5-1 .5 0 .9.2 1.2.5.3.4.3.9.3 1.4v4.7c0 .1-.1.2-.2.2h-1.1c-.1 0-.2-.1-.2-.2v-4c0-.3 0-.7-.1-.9-.1-.3-.3-.4-.6-.4-.3 0-.6.2-.7.5-.1.2-.1.6-.1.9v3.9c0 .1-.1.2-.2.2H7.5c-.1 0-.2-.1-.2-.2v-4c0-.3 0-.7-.1-.9-.1-.3-.3-.4-.6-.4-.3 0-.6.2-.7.5-.1.2-.1.6-.1.9v3.9c.1.1 0 .2-.1.2z"/>
                  </svg>
                </div>
                <div class="platform-name">Amazon</div>
              </div>
              <div class="platform-node ebay" data-platform="eBay">
                <div class="modern-platform-icon ebay-modern">
                  <svg viewBox="0 0 24 24" fill="currentColor" class="platform-svg">
                    <text x="12" y="16" text-anchor="middle" class="platform-text">eBay</text>
                  </svg>
                </div>
                <div class="platform-name">eBay</div>
              </div>
              <div class="platform-node shopify" data-platform="Shopify">
                <div class="modern-platform-icon shopify-modern">
                  <svg viewBox="0 0 24 24" fill="currentColor" class="platform-svg">
                    <path d="M14.4 8.9c0-.2-.2-.3-.3-.3-1.2 0-2.5.9-2.8 2.8-.8.1-1.7.2-2.4.3.7-2.5 2.4-5.2 5.4-5.2 0 0 0 1 .1 2.4zM13.4 9c-.1 0-.2.1-.2.1-.5 0-1 .2-1.4.5-.4.3-.6.7-.8 1.2-.2.4-.3.9-.3 1.4v.1c-.5.1-1 .1-1.5.2.3-1.4 1.3-2.9 3.1-2.9h.5c.3-.2.5-.3.6-.6z"/>
                    <path d="M15.5 7.2c-.2-1.1-.6-2.5-.6-2.5s-1.4-.1-1.8-.1c-1.3 0-1.4.8-1.4 1 0 1.1 2.9.2 3.8 1.6z"/>
                    <path d="M15.4 7.7c-.4-.3-.9-.4-1.5-.4h-.1c0-.1-.1-.3-.1-.4-.5-1.5-2.8-.9-3.7-.6-.1 0-.2.1-.3.1-.9-2.5-3-4.2-3.2-4.3L6 1.6l-.4.9c-.6 1.6-1.2 4-.8 6 .3 1.5 1 2.8 2.1 3.8 1 .9 2.3 1.5 3.8 1.7 1.6.2 3.2-.1 4.5-.9 1.2-.8 2.1-2 2.3-3.4.1-1.2-.4-1.7-2.1-2z"/>
                    <path d="M12 18c-3.3 0-6-2.7-6-6s2.7-6 6-6 6 2.7 6 6-2.7 6-6 6z"/>
                  </svg>
                </div>
                <div class="platform-name">Shopify</div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- AI中心节点 -->
        <div class="ai-center">
          <div class="ai-brain">
            <div class="ai-core">
              <div class="ai-service-icon">
                <div class="ai-head">
                  <div class="ai-eye left"></div>
                  <div class="ai-eye right"></div>
                  <div class="ai-antenna"></div>
                </div>
                <div class="ai-body">
                  <div class="ai-screen">
                    <div class="message-line"></div>
                    <div class="message-line short"></div>
                  </div>
                </div>
              </div>
            </div>
            <div class="ai-pulse"></div>
          </div>
          <div class="ai-label">AI智能客服</div>
        </div>
        
        <!-- 社交媒体节点组 - 右侧 -->
        <div class="node-group social-nodes">
          <div class="platform-section">
            <!-- 国内社交媒体 -->
            <div class="domestic-platforms">
              <div class="section-label">国内社交</div>
              <div class="social-node wechat" data-social="微信">
                <div class="modern-social-icon wechat-modern">
                  <svg viewBox="0 0 24 24" fill="currentColor" class="platform-svg">
                    <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 4.882-1.932 7.621-.72-.12-.019-.245-.027-.37-.027C14.95 9.627 9.86 6.559 8.691 2.188z"/>
                    <path d="M23.999 16.068c0-3.31-3.018-5.99-6.74-5.99-3.722 0-6.74 2.68-6.74 5.99 0 3.31 3.018 5.99 6.74 5.99.637 0 1.252-.081 1.834-.227a.72.72 0 0 1 .598.081l1.585.927a.269.269 0 0 0 .138.045c.134 0 .241-.109.241-.243 0-.06-.024-.117-.04-.176l-.325-1.234a.492.492 0 0 1 .177-.554c1.528-1.12 2.532-2.786 2.532-4.609z"/>
                  </svg>
                </div>
                <div class="platform-name">微信</div>
              </div>
              <div class="social-node douyin" data-social="抖音">
                <div class="modern-social-icon douyin-modern">
                  <svg viewBox="0 0 24 24" fill="currentColor" class="platform-svg">
                    <path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/>
                  </svg>
                </div>
                <div class="platform-name">抖音</div>
              </div>
              <div class="social-node xiaohongshu" data-social="小红书">
                <div class="modern-social-icon xiaohongshu-modern">
                  <svg viewBox="0 0 24 24" fill="currentColor" class="platform-svg">
                    <path d="M12 2L2 7v10c0 5.55 3.84 9.74 9 10.5 5.16-.76 9-4.95 9-10.5V7l-10-5z"/>
                    <path d="M12 4.5L4.5 8.5v8c0 4.1 2.9 7.3 7.5 8 4.6-.7 7.5-3.9 7.5-8v-8L12 4.5z" fill="white"/>
                    <text x="12" y="16" text-anchor="middle" class="platform-text" fill="#fe2d55">小红书</text>
                  </svg>
                </div>
                <div class="platform-name">小红书</div>
              </div>
            </div>
            
            <!-- 国外社交媒体 -->
            <div class="international-platforms">
              <div class="section-label">国外社交</div>
              <div class="social-node facebook" data-social="Facebook">
                <div class="modern-social-icon facebook-modern">
                  <svg viewBox="0 0 24 24" fill="currentColor" class="platform-svg">
                    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                  </svg>
                </div>
                <div class="platform-name">Facebook</div>
              </div>
              <div class="social-node instagram" data-social="Instagram">
                <div class="modern-social-icon instagram-modern">
                  <svg viewBox="0 0 24 24" fill="currentColor" class="platform-svg">
                    <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.354-.2-6.782-2.618-2.618-6.979-6.98-.059-1.28.059-1.689.073-4.948.073zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                  </svg>
                </div>
                <div class="platform-name">Instagram</div>
              </div>
              <div class="social-node twitter" data-social="Twitter">
                <div class="modern-social-icon twitter-modern">
                  <svg viewBox="0 0 24 24" fill="currentColor" class="platform-svg">
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                  </svg>
                </div>
                <div class="platform-name">Twitter</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 连接线动画 -->
      <svg class="connection-lines" viewBox="0 0 100 100" preserveAspectRatio="none">
        <defs>
          <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#4facfe;stop-opacity:0"/>
            <stop offset="50%" style="stop-color:#00f2fe;stop-opacity:1"/>
            <stop offset="100%" style="stop-color:#4facfe;stop-opacity:0"/>
          </linearGradient>
          <linearGradient id="lineGradient2" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#ff6b6b;stop-opacity:0"/>
            <stop offset="50%" style="stop-color:#ffa726;stop-opacity:1"/>
            <stop offset="100%" style="stop-color:#ff6b6b;stop-opacity:0"/>
          </linearGradient>
          <linearGradient id="lineGradient3" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#4ecdc4;stop-opacity:0"/>
            <stop offset="50%" style="stop-color:#45b7d1;stop-opacity:1"/>
            <stop offset="100%" style="stop-color:#4ecdc4;stop-opacity:0"/>
          </linearGradient>
          <linearGradient id="lineGradient4" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#a8e6cf;stop-opacity:0"/>
            <stop offset="50%" style="stop-color:#88d8a3;stop-opacity:1"/>
            <stop offset="100%" style="stop-color:#a8e6cf;stop-opacity:0"/>
          </linearGradient>
          <linearGradient id="lineGradient5" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#ffaaa5;stop-opacity:0"/>
            <stop offset="50%" style="stop-color:#ff8a95;stop-opacity:1"/>
            <stop offset="100%" style="stop-color:#ffaaa5;stop-opacity:0"/>
          </linearGradient>
        </defs>
        <path class="connection-line line1" d="M15,20 Q50,10 85,20" stroke="url(#lineGradient)" stroke-width="1.2" fill="none"/>
        <path class="connection-line line2" d="M15,30 Q50,20 85,30" stroke="url(#lineGradient2)" stroke-width="1.0" fill="none"/>
        <path class="connection-line line3" d="M15,50 Q50,40 85,50" stroke="url(#lineGradient)" stroke-width="1.5" fill="none"/>
        <path class="connection-line line4" d="M15,70 Q50,60 85,70" stroke="url(#lineGradient3)" stroke-width="1.0" fill="none"/>
        <path class="connection-line line5" d="M15,80 Q50,90 85,80" stroke="url(#lineGradient4)" stroke-width="1.2" fill="none"/>
        <path class="connection-line line6" d="M15,40 Q50,30 85,40" stroke="url(#lineGradient5)" stroke-width="0.8" fill="none"/>
        <path class="connection-line line7" d="M15,60 Q50,70 85,60" stroke="url(#lineGradient2)" stroke-width="1.0" fill="none"/>
      </svg>
      
      <!-- AI功能展示气泡 - 分散在中央区域 -->
      <div class="ai-features-display">
        <!-- 第一层功能气泡 -->
        <div class="feature-bubble feature-1" style="top: 23%; left: 25%;">
          <div class="feature-icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
          </div>
          <span class="feature-text">用户意图识别</span>
        </div>
        
        <div class="feature-bubble feature-2" style="top: 33%; left: 68%;">
          <div class="feature-icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
              <path d="M17.3 11c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z"/>
            </svg>
          </div>
          <span class="feature-text">语音识别与多模态</span>
        </div>
        
        <div class="feature-bubble feature-3" style="top: 38%; left: 30%;">
          <div class="feature-icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
          </div>
          <span class="feature-text">多平台数据同步</span>
        </div>
        
        <div class="feature-bubble feature-4" style="top: 45%; left: 68%;">
          <div class="feature-icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
              <circle cx="12" cy="12" r="3"/>
              <path d="M12 2l2 4h4l-3 3 1 4-4-2-4 2 1-4-3-3h4z"/>
            </svg>
          </div>
          <span class="feature-text">知识图谱构建</span>
        </div>
        
        <div class="feature-bubble feature-5" style="top: 50%; left: 25%;">
          <div class="feature-icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
            </svg>
          </div>
          <span class="feature-text">数据统计与分析</span>
        </div>
        
        <div class="feature-bubble feature-6" style="top: 65%; left: 65%;">
          <div class="feature-icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
            </svg>
          </div>
          <span class="feature-text">情感分析识别</span>
        </div>
        
        <div class="feature-bubble feature-7" style="top: 65%; left: 25%;">
          <div class="feature-icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M16 4c0-1.11.89-2 2-2s2 .89 2 2-.89 2-2 2-2-.89-2-2zm4 18v-6h2.5l-2.54-7.63A2.5 2.5 0 0 0 17.5 7H16c-.8 0-1.56.31-2.13.88L12 10.5 10.13 7.88A2.99 2.99 0 0 0 8 7H6.5c-1.38 0-2.54 1.12-2.54 2.5L1.5 16H4v6h2v-6h2l2-3 2 3h2v6h2z"/>
            </svg>
          </div>
          <span class="feature-text">人工客服转接</span>
        </div>
        
        <div class="feature-bubble feature-8" style="top: 22%; left: 63%;">
          <div class="feature-icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm3.5 6L12 10.5 8.5 8 12 5.5 15.5 8zM8.5 16L12 13.5 15.5 16 12 18.5 8.5 16z"/>
            </svg>
          </div>
          <span class="feature-text">个性化推荐</span>
        </div>
        
        <div class="feature-bubble feature-9" style="top: 70%; left: 30%;">
          <div class="feature-icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
              <circle cx="12" cy="12" r="1"/>
            </svg>
          </div>
          <span class="feature-text">24小时智能在线</span>
        </div>
      </div>
    </div>
    
    <!-- 登录表单 -->
    <div class="login-box">
      <div class="login-header">
        <div class="logo-container">
          <div class="logo-icon">
            <div class="ai-symbol">
              <div class="ai-service-icon">
                <div class="ai-head">
                  <div class="ai-eye left"></div>
                  <div class="ai-eye right"></div>
                  <div class="ai-antenna"></div>
                </div>
                <div class="ai-body">
                  <div class="ai-screen">
                    <div class="message-line"></div>
                    <div class="message-line short"></div>
                  </div>
                </div>
              </div>
            </div>
            <div class="tech-rings">
              <div class="ring ring1"></div>
              <div class="ring ring2"></div>
              <div class="ring ring3"></div>
            </div>
          </div>
          <h1 class="logo-title">ShopTalk AI</h1>
        </div>
        <p class="login-subtitle">全球电商智能客服连接平台</p>
        <div class="feature-tags">
          <span class="feature-tag">🔗 全平台连接</span>
          <span class="feature-tag">🤖 AI驱动</span>
          <span class="feature-tag">📊 智能分析</span>
        </div>
      </div>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            prefix-icon="User"
            size="large"
            class="smart-input"
          >
            <template #suffix>
              <div class="input-indicator"></div>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            size="large"
            class="smart-input"
            show-password
          >
            <template #suffix>
              <div class="input-indicator"></div>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item prop="captcha">
          <div class="captcha-row">
            <el-input
              v-model="loginForm.captcha"
              placeholder="验证码"
              size="large"
              class="smart-input captcha-input"
            >
              <template #prefix>
                <i class="captcha-prefix-icon">🔐</i>
              </template>
            </el-input>
            <div class="smart-captcha" @click="refreshCaptcha">
              <img :src="captchaUrl" alt="验证码" />
              <div class="captcha-overlay">
                <i class="refresh-icon">🔄</i>
              </div>
            </div>
          </div>
        </el-form-item>
        
        <el-form-item>
          <div class="login-options">
            <el-checkbox v-model="loginForm.remember" class="smart-checkbox">
              <span class="checkbox-text">记住登录</span>
            </el-checkbox>
            <el-link type="primary" :underline="false" @click="handleForgotPassword" class="forgot-link">
              忘记密码？
            </el-link>
          </div>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="ai-login-btn"
            :loading="loading"
            @click="handleLogin"
          >
            <span v-if="!loading" class="btn-content">
              <i class="btn-icon">⚡</i>
              登录
            </span>
            <span v-else class="btn-loading">
              <i class="loading-icon">🔄</i>
              AI验证中...
            </span>
          </el-button>
        </el-form-item>
      </el-form>
      
      <!-- 平台连接状态 -->
      <div class="platform-status">
        <div class="status-title">实时连接状态</div>
        <div class="platform-indicators">
          <div class="indicator active" title="淘宝">
            <span class="dot"></span>淘宝
          </div>
          <div class="indicator active" title="京东">
            <span class="dot"></span>京东
          </div>
          <div class="indicator active" title="微信">
            <span class="dot"></span>微信
          </div>
          <div class="indicator pending" title="Facebook">
            <span class="dot"></span>Facebook
          </div>
        </div>
      </div>
      
      <!-- 版权信息 -->
      <div class="copyright">
        <p>&copy; 2024 ShopTalk AI. 连接全球电商，智能服务未来</p>
      </div>
    </div>
    
    <!-- AI智能加载组件 -->
    <AILoadingComponent :visible="showAILoading" />
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, FormInstance } from 'element-plus'
import { useUserStore } from '@/stores/user'
import type { LoginForm } from '@/types/user'
import AILoadingComponent from '@/components/AILoadingComponent.vue'

const router = useRouter()
const userStore = useUserStore()
const loginFormRef = ref<FormInstance>()

const loading = ref(false)
const showAILoading = ref(false)
const captchaUrl = ref('/api/auth/captcha/')

const loginForm = reactive<LoginForm>({
  username: '',
  password: '',
  captcha: '',
  remember: false
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  captcha: [
    { required: true, message: '请输入验证码', trigger: 'blur' }
  ]
}

// 刷新验证码
const refreshCaptcha = () => {
  captchaUrl.value = `/api/auth/captcha/?t=${Date.now()}`
}

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  try {
    await loginFormRef.value.validate()
    loading.value = true
    showAILoading.value = true
    
    // 模拟AI验证过程
    await new Promise(resolve => setTimeout(resolve, 3000))
    
    const result = await userStore.loginAction(loginForm)
    
    if (result.success) {
      // 延迟一秒显示成功消息，让用户看到连接完成
      setTimeout(() => {
        showAILoading.value = false
        ElMessage.success('AI验证成功，欢迎使用ShopTalk!')
        router.push('/')
      }, 1000)
    } else {
      showAILoading.value = false
      ElMessage.error(result.message)
      refreshCaptcha()
    }
  } catch (error) {
    console.error('表单验证失败:', error)
    showAILoading.value = false
  } finally {
    loading.value = false
  }
}

// 处理忘记密码
const handleForgotPassword = () => {
  ElMessage.info('请联系管理员重置密码，或使用测试账号：用户名/密码都是 kejishu')
}

// 初始化
refreshCaptcha()
</script>

<style lang="scss" scoped>
.login-container {
  position: relative;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
  overflow: hidden;
}

.ai-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  
  .glassmorphism-container {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 80%;
    height: 60%;
    pointer-events: none;
    z-index: 0;
    
    .absolute {
      position: absolute;
    }
    
    .inset-0 {
      top: 0;
      right: 0;
      bottom: 0;
      left: 0;
    }
    
    .bg-black\/20 {
      background-color: rgba(0, 0, 0, 0.2);
    }
    
    .backdrop-blur-xl {
      backdrop-filter: blur(24px);
    }
    
    .rounded-2xl {
      border-radius: 1rem;
    }
    
    .border {
      border-width: 1px;
      border-style: solid;
    }
    
    .border-white\/10 {
      border-color: rgba(255, 255, 255, 0.1);
    }
    
    .shadow-2xl {
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    }
  }
}

.network-nodes {
  position: absolute;
  width: 100%;
  height: 100%;
  
  .node-group {
    position: absolute;
    display: flex;
    flex-direction: column;
    
    &.ecommerce-nodes {
      top: 15%;
      left: 5%;
      width: 250px;
    }
    
    &.social-nodes {
      top: 15%;
      right: 5%;
      width: 250px;
    }
    
    .platform-section {
      display: flex;
      flex-direction: column;
      gap: 40px;
      
      .domestic-platforms,
      .international-platforms {
        display: flex;
        flex-direction: column;
        gap: 20px;
        
        .section-label {
          font-size: 14px;
          font-weight: bold;
          color: rgba(74, 172, 254, 0.8);
          text-align: center;
          margin-bottom: 10px;
          padding: 8px 16px;
          background: rgba(74, 172, 254, 0.1);
          border: 1px solid rgba(74, 172, 254, 0.3);
          border-radius: 20px;
          backdrop-filter: blur(10px);
          position: relative;
          
          &::before {
            content: '';
            position: absolute;
            top: 50%;
            left: -10px;
            width: 6px;
            height: 6px;
            background: #4facfe;
            border-radius: 50%;
            transform: translateY(-50%);
            animation: labelPulse 2s ease-in-out infinite;
          }
          
          &::after {
            content: '';
            position: absolute;
            top: 50%;
            right: -10px;
            width: 6px;
            height: 6px;
            background: #4facfe;
            border-radius: 50%;
            transform: translateY(-50%);
            animation: labelPulse 2s ease-in-out infinite 1s;
          }
        }
        
        .platform-node,
        .social-node {
          position: relative;
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 12px 16px;
          background: rgba(26, 31, 46, 0.8);
          border: 2px solid rgba(74, 172, 254, 0.2);
          border-radius: 16px;
          transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
          backdrop-filter: blur(15px);
          animation: nodeSlideIn 0.8s ease-out;
          
          &:hover {
            transform: translateX(10px) scale(1.05);
            border-color: #4facfe;
            box-shadow: 0 8px 32px rgba(74, 172, 254, 0.3);
            background: rgba(74, 172, 254, 0.1);
          }
          
          .modern-platform-icon,
          .modern-social-icon {
            position: relative;
            width: 48px;
            height: 48px;
            clip-path: url(#squircleClip);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
            cursor: pointer;
            transform: translateZ(0);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            backdrop-filter: blur(12px);
            flex-shrink: 0;
            
            .platform-svg {
              width: 32px;
              height: 32px;
              color: white;
              
              .platform-text {
                fill: currentColor;
                font-size: 7px;
                font-weight: 900;
                font-family: 'Arial', 'Helvetica', sans-serif;
              }
            }
            
            &:hover {
              transform: scale(1.1) rotate(5deg);
              box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4);
            }
          }
          
          .platform-name {
            font-size: 14px;
            font-weight: 600;
            color: #ffffff;
            flex: 1;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
          }
          
          &::before {
            content: '';
            position: absolute;
            left: -6px;
            top: 50%;
            width: 4px;
            height: 0;
            background: linear-gradient(180deg, #4facfe, #00f2fe);
            border-radius: 2px;
            transform: translateY(-50%);
            transition: height 0.3s ease;
          }
          
          &:hover::before {
            height: 60%;
          }
        }
      }
      
      .domestic-platforms {
        .platform-node,
        .social-node {
          animation-delay: 0.2s;
          
          &:nth-child(2) { animation-delay: 0.3s; }
          &:nth-child(3) { animation-delay: 0.4s; }
          &:nth-child(4) { animation-delay: 0.5s; }
        }
      }
      
      .international-platforms {
        .platform-node,
        .social-node {
          animation-delay: 0.6s;
          
          &:nth-child(2) { animation-delay: 0.7s; }
          &:nth-child(3) { animation-delay: 0.8s; }
          &:nth-child(4) { animation-delay: 0.9s; }
        }
      }
    }
  }
  
  // 保持现有的平台图标样式
  .modern-platform-icon {
    &.taobao-modern {
      background: linear-gradient(135deg, rgba(255, 69, 0, 0.8), rgba(255, 99, 71, 0.6));
      box-shadow: 0 8px 32px rgba(255, 69, 0, 0.3);
    }
    
    &.jd-modern {
      background: linear-gradient(135deg, rgba(225, 37, 27, 0.8), rgba(255, 68, 68, 0.6));
      box-shadow: 0 8px 32px rgba(225, 37, 27, 0.3);
    }
    
    &.pdd-modern {
      background: linear-gradient(135deg, rgba(224, 32, 32, 0.8), rgba(255, 71, 87, 0.6));
      box-shadow: 0 8px 32px rgba(224, 32, 32, 0.3);
    }
    
    &.amazon-modern {
      background: linear-gradient(135deg, rgba(255, 149, 0, 0.8), rgba(255, 179, 71, 0.6));
      box-shadow: 0 8px 32px rgba(255, 149, 0, 0.3);
    }
    
    &.ebay-modern {
      background: linear-gradient(135deg, rgba(230, 211, 32, 0.8), rgba(255, 242, 0, 0.6));
      box-shadow: 0 8px 32px rgba(230, 211, 32, 0.3);
    }
    
    &.shopify-modern {
      background: linear-gradient(135deg, rgba(122, 181, 92, 0.8), rgba(139, 195, 74, 0.6));
      box-shadow: 0 8px 32px rgba(122, 181, 92, 0.3);
    }
  }
  
  .modern-social-icon {
    &.wechat-modern {
      background: linear-gradient(135deg, rgba(7, 193, 96, 0.8), rgba(26, 173, 25, 0.6));
      box-shadow: 0 8px 32px rgba(7, 193, 96, 0.3);
    }
    
    &.douyin-modern {
      background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(255, 0, 80, 0.7));
      box-shadow: 0 8px 32px rgba(255, 0, 80, 0.4);
      
      .platform-svg {
        color: #ff0050;
      }
    }
    
    &.xiaohongshu-modern {
      background: linear-gradient(135deg, rgba(254, 44, 85, 0.8), rgba(255, 71, 87, 0.6));
      box-shadow: 0 8px 32px rgba(254, 44, 85, 0.3);
    }
    
    &.facebook-modern {
      background: linear-gradient(135deg, rgba(66, 103, 178, 0.8), rgba(91, 140, 233, 0.6));
      box-shadow: 0 8px 32px rgba(66, 103, 178, 0.3);
    }
    
    &.instagram-modern {
      background: linear-gradient(135deg, rgba(245, 96, 64, 0.8), rgba(252, 175, 69, 0.6));
      box-shadow: 0 8px 32px rgba(245, 96, 64, 0.3);
    }
    
    &.twitter-modern {
      background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(29, 161, 242, 0.7));
      box-shadow: 0 8px 32px rgba(29, 161, 242, 0.3);
    }
  }
  
  .ai-center {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    z-index: 10;
    
    .ai-brain {
      position: relative;
      width: 100px;
      height: 100px;
      
      .ai-core {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 2;
        animation: aiPulse 2s ease-in-out infinite;
        border: 3px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 0 30px rgba(74, 172, 254, 0.6);
        
        .ai-service-icon {
          width: 60px;
          height: 60px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          
          .ai-head {
            position: relative;
            width: 20px;
            height: 15px;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 10px 10px 5px 5px;
            margin-bottom: 2px;
            
            .ai-eye {
              position: absolute;
              width: 2.5px;
              height: 2.5px;
              background: #4facfe;
              border-radius: 50%;
              top: 5px;
              animation: eyeBlink 3s ease-in-out infinite;
              
              &.left { left: 5px; }
              &.right { right: 5px; }
            }
            
            .ai-antenna {
              position: absolute;
              width: 1px;
              height: 5px;
              background: rgba(255, 255, 255, 0.8);
              top: -5px;
              left: 50%;
              transform: translateX(-50%);
              border-radius: 0.5px;
              
              &::after {
                content: '';
                position: absolute;
                width: 3px;
                height: 3px;
                background: #4facfe;
                border-radius: 50%;
                top: -1.5px;
                left: 50%;
                transform: translateX(-50%);
                animation: antennaPulse 2s ease-in-out infinite;
              }
            }
          }
          
          .ai-body {
            width: 17px;
            height: 12px;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 2px;
            display: flex;
            align-items: center;
            justify-content: center;
            
            .ai-screen {
              width: 12px;
              height: 7px;
              background: #1a1a2e;
              border-radius: 1px;
              display: flex;
              flex-direction: column;
              justify-content: center;
              gap: 1px;
              padding: 1px;
              
              .message-line {
                height: 0.5px;
                background: #4facfe;
                border-radius: 0.25px;
                animation: messageFlow 2s ease-in-out infinite;
                
                &.short {
                  width: 60%;
                  animation-delay: 0.5s;
                }
              }
            }
          }
        }
      }
      
      .ai-pulse {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: rgba(74, 172, 254, 0.3);
        animation: pulse 2s ease-in-out infinite;
      }
    }
    
    .ai-label {
      margin-top: 12px;
      color: #ffffff;
      font-weight: bold;
      font-size: 16px;
      text-shadow: 0 2px 8px rgba(74, 172, 254, 0.8);
    }
  }
}

.connection-lines {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  z-index: 1;
  
  .connection-line {
    stroke-dasharray: 8 8;
    animation: dashFlow 4s linear infinite;
    
    &.line1 { animation-delay: 0s; }
    &.line2 { animation-delay: 0.5s; }
    &.line3 { animation-delay: 1s; }
    &.line4 { animation-delay: 1.5s; }
    &.line5 { animation-delay: 2s; }
    &.line6 { animation-delay: 2.5s; }
    &.line7 { animation-delay: 3s; }
  }
}

.ai-features-display {
  /* 让气泡区域与登录表单上下对齐，左右适当收缩，z-index 比 .login-box 低 */
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-around;
  align-items: center;
  pointer-events: none;
}

.ai-features-display .feature-bubble {
  position: absolute;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  background: rgba(26, 31, 46, 0.85);
  border: 1.5px solid rgba(74, 172, 254, 0.25);
  border-radius: 16px;
  backdrop-filter: blur(12px);
  box-shadow: 0 4px 16px rgba(74, 172, 254, 0.10);
  min-width: 90px;
  max-width: 140px;
  font-size: 10px;
  opacity: 0;
  animation: featureSlideIn 0.8s ease-out forwards;
  pointer-events: auto;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 2;
}

.ai-features-display .feature-bubble .feature-icon {
  width: 16px;
  height: 16px;
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ai-features-display .feature-bubble .feature-icon svg {
  width: 12px;
  height: 12px;
}

.ai-features-display .feature-bubble .feature-text {
  font-size: 10px;
  font-weight: 500;
  white-space: nowrap;
}

/* 左侧功能气泡 */
.feature-bubble.feature-1 { 
  left: 16%; 
  top: 20%;
}
.feature-bubble.feature-3 { 
  left: 26%; 
  top: 40%;
}
.feature-bubble.feature-5 { 
  left: 26%; 
  top: 60%;
}
.feature-bubble.feature-7 { 
  left: 26%; 
  top: 80%;
}
.feature-bubble.feature-9 { 
  left: 28%; 
  top: 70%;
}

/* 右侧功能气泡 */
.feature-bubble.feature-2 { 
  right: 16%; 
  top: 20%;
}
.feature-bubble.feature-4 { 
  right: 16%; 
  top: 40%;
}
.feature-bubble.feature-6 { 
  right: 16%; 
  top: 60%;
}
.feature-bubble.feature-8 { 
  right: 16%; 
  top: 80%;
}

/* 响应式进一步缩小 */
@media (max-width: 1200px) {
  .ai-features-display .feature-bubble {
    min-width: 80px;
    max-width: 120px;
    padding: 4px 8px;
    font-size: 9px;
  }
  .ai-features-display .feature-bubble .feature-icon {
    width: 14px;
    height: 14px;
  }
  .ai-features-display .feature-bubble .feature-icon svg {
    width: 10px;
    height: 10px;
  }
  .ai-features-display .feature-bubble .feature-text {
    font-size: 9px;
  }
  
  /* 调整左侧功能气泡位置 */
  .feature-bubble.feature-1,
  .feature-bubble.feature-3,
  .feature-bubble.feature-5,
  .feature-bubble.feature-7,
  .feature-bubble.feature-9 {
    left: 16%;
  }
  
  /* 调整右侧功能气泡位置 */
  .feature-bubble.feature-2,
  .feature-bubble.feature-4,
  .feature-bubble.feature-6,
  .feature-bubble.feature-8 {
    right: 16%;
  }
}

@media (max-width: 768px) {
  .ai-features-display .feature-bubble {
    min-width: 70px;
    max-width: 100px;
    padding: 3px 6px;
    font-size: 8px;
  }
  .ai-features-display .feature-bubble .feature-icon {
    width: 12px;
    height: 12px;
  }
  .ai-features-display .feature-bubble .feature-icon svg {
    width: 8px;
    height: 8px;
  }
  .ai-features-display .feature-bubble .feature-text {
    font-size: 8px;
  }
  
  /* 移动版隐藏部分气泡，保留重要的 */
  .feature-bubble.feature-3,
  .feature-bubble.feature-5,
  .feature-bubble.feature-7,
  .feature-bubble.feature-9 {
    display: none;
  }
  
  /* 调整左侧功能气泡位置 */
  .feature-bubble.feature-1 {
    left: 16%;
  }
  
  /* 调整右侧功能气泡位置 */
  .feature-bubble.feature-2,
  .feature-bubble.feature-4,
  .feature-bubble.feature-6,
  .feature-bubble.feature-8 {
    right: 16%;
  }
}

.login-box {
  position: relative;
  z-index: 3; /* 提高z-index使登录框位于气泡之上 */
  width: 450px;
  padding: 48px;
  background: rgba(26, 31, 46, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(74, 172, 254, 0.2);
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  animation: slideInUp 0.8s ease-out;
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
  
  .logo-container {
    position: relative;
    margin-bottom: 16px;
    
    .logo-icon {
      position: relative;
      display: inline-block;
      margin-bottom: 16px;
      
      .ai-symbol {
        position: relative;
        z-index: 2;
        filter: drop-shadow(0 0 20px rgba(74, 172, 254, 0.8));
        
        .ai-service-icon {
          width: 36px;
          height: 36px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          
          .ai-head {
            position: relative;
            width: 20px;
            height: 15px;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 10px 10px 5px 5px;
            margin-bottom: 2px;
            
            .ai-eye {
              position: absolute;
              width: 2.5px;
              height: 2.5px;
              background: #4facfe;
              border-radius: 50%;
              top: 5px;
              animation: eyeBlink 3s ease-in-out infinite;
              
              &.left { left: 5px; }
              &.right { right: 5px; }
            }
            
            .ai-antenna {
              position: absolute;
              width: 1px;
              height: 5px;
              background: rgba(255, 255, 255, 0.8);
              top: -5px;
              left: 50%;
              transform: translateX(-50%);
              border-radius: 0.5px;
              
              &::after {
                content: '';
                position: absolute;
                width: 3px;
                height: 3px;
                background: #4facfe;
                border-radius: 50%;
                top: -1.5px;
                left: 50%;
                transform: translateX(-50%);
                animation: antennaPulse 2s ease-in-out infinite;
              }
            }
          }
          
          .ai-body {
            width: 17px;
            height: 12px;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 2px;
            display: flex;
            align-items: center;
            justify-content: center;
            
            .ai-screen {
              width: 12px;
              height: 7px;
              background: #1a1a2e;
              border-radius: 1px;
              display: flex;
              flex-direction: column;
              justify-content: center;
              gap: 1px;
              padding: 1px;
              
              .message-line {
                height: 0.5px;
                background: #4facfe;
                border-radius: 0.25px;
                animation: messageFlow 2s ease-in-out infinite;
                
                &.short {
                  width: 60%;
                  animation-delay: 0.5s;
                }
              }
            }
          }
        }
      }
      
      .tech-rings {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        
        .ring {
          position: absolute;
          border: 2px solid rgba(74, 172, 254, 0.3);
          border-radius: 50%;
          
          &.ring1 {
            width: 80px;
            height: 80px;
            animation: ringRotate 8s linear infinite;
          }
          
          &.ring2 {
            width: 100px;
            height: 100px;
            animation: ringRotate 12s linear infinite reverse;
          }
          
          &.ring3 {
            width: 120px;
            height: 120px;
            animation: ringRotate 16s linear infinite;
          }
        }
      }
    }
    
    .logo-title {
      font-size: 32px;
      font-weight: bold;
      background: $gradient-tech;
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin: 0;
    }
  }
  
  .login-subtitle {
    color: $text-secondary;
    font-size: 16px;
    margin-bottom: 16px;
  }
  
  .feature-tags {
    display: flex;
    justify-content: center;
    gap: 12px;
    flex-wrap: wrap;
    
    .feature-tag {
      padding: 4px 12px;
      background: rgba(74, 172, 254, 0.1);
      border: 1px solid rgba(74, 172, 254, 0.3);
      border-radius: 16px;
      color: $text-secondary;
      font-size: 12px;
      backdrop-filter: blur(10px);
    }
  }
}

.login-form {
  .smart-input {
    margin-bottom: 8px;
    
    :deep(.el-input__wrapper) {
      background: rgba(255, 255, 255, 0.03);
      border: 2px solid rgba(74, 172, 254, 0.2);
      border-radius: 12px;
      transition: all 0.3s ease;
      height: 50px;
      
      &:hover {
        border-color: rgba(74, 172, 254, 0.5);
        box-shadow: 0 0 0 3px rgba(74, 172, 254, 0.1);
      }
      
      &.is-focus {
        border-color: $primary-color;
        box-shadow: 0 0 0 3px rgba(74, 172, 254, 0.2);
        background: rgba(74, 172, 254, 0.05);
      }
    }
    
    :deep(.el-input__inner) {
      color: $text-primary;
      font-size: 16px;
      
      &::placeholder {
        color: $text-placeholder;
      }
    }
    
    .input-indicator {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: rgba(74, 172, 254, 0.5);
      animation: indicatorPulse 2s ease-in-out infinite;
    }
  }
}

.captcha-row {
  display: flex;
  gap: 16px;
  align-items: center;
  
  .captcha-input {
    flex: 1;
  }
  
  .smart-captcha {
    position: relative;
    width: 140px;
    height: 50px;
    cursor: pointer;
    border-radius: 12px;
    overflow: hidden;
    border: 2px solid rgba(74, 172, 254, 0.2);
    transition: all 0.3s ease;
    
    &:hover {
      border-color: $primary-color;
      transform: scale(1.05);
    }
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    
    .captcha-overlay {
      position: absolute;
      top: 0;
      right: 0;
      width: 30px;
      height: 100%;
      background: rgba(74, 172, 254, 0.2);
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0;
      transition: opacity 0.3s ease;
      
      .refresh-icon {
        font-size: 14px;
        animation: spin 2s linear infinite;
      }
    }
    
    &:hover .captcha-overlay {
      opacity: 1;
    }
  }
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  margin-bottom: 8px;
  
  .smart-checkbox {
    :deep(.el-checkbox__label) {
      color: $text-secondary;
      
      .checkbox-text {
        font-size: 14px;
      }
    }
  }
  
  .forgot-link {
    font-size: 14px;
    
    &:hover {
      text-shadow: 0 0 8px rgba(74, 172, 254, 0.6);
    }
  }
}

.ai-login-btn {
  width: 100%;
  height: 56px;
  font-size: 18px;
  font-weight: 600;
  border: none;
  border-radius: 12px;
  background: $gradient-tech;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  
  .btn-content, .btn-loading {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    
    .btn-icon, .loading-icon {
      font-size: 20px;
      animation: iconGlow 2s ease-in-out infinite;
    }
    
    .loading-icon {
      animation: spin 1s linear infinite;
    }
  }
  
  &:hover:not(:disabled) {
    transform: translateY(-3px);
    box-shadow: 0 12px 40px rgba(74, 172, 254, 0.4);
  }
  
  &:active {
    transform: translateY(-1px);
  }
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: left 0.5s;
  }
  
  &:hover::before {
    left: 100%;
  }
}

.platform-status {
  margin-top: 32px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(74, 172, 254, 0.1);
  border-radius: 12px;
  
  .status-title {
    color: $text-secondary;
    font-size: 12px;
    margin-bottom: 12px;
    text-align: center;
  }
  
  .platform-indicators {
    display: flex;
    justify-content: space-between;
    
    .indicator {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 11px;
      color: $text-tertiary;
      
      .dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: #666;
      }
      
      &.active .dot {
        background: $success-color;
        box-shadow: 0 0 8px rgba(82, 196, 26, 0.6);
        animation: statusPulse 2s ease-in-out infinite;
      }
      
      &.pending .dot {
        background: $warning-color;
        animation: statusBlink 1s ease-in-out infinite;
      }
    }
  }
}

.copyright {
  text-align: center;
  margin-top: 24px;
  color: $text-tertiary;
  font-size: 12px;
}

// 动画定义
@keyframes dashFlow {
  0% { stroke-dashoffset: 0; }
  100% { stroke-dashoffset: 32; }
}

@keyframes featureSlideIn {
  0% {
    opacity: 0;
    transform: translateY(40px) scale(0.8);
  }
  60% {
    opacity: 1;
    transform: translateY(-10px) scale(1.05);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes slideInUp {
  from {
    transform: translateY(60px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes ringRotate {
  from { transform: translate(-50%, -50%) rotate(0deg); }
  to { transform: translate(-50%, -50%) rotate(360deg); }
}

@keyframes aiPulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); }
  50% { transform: translate(-50%, -50%) scale(1.1); }
}

@keyframes pulse {
  0% { transform: translate(-50%, -50%) scale(1); opacity: 0.7; }
  50% { transform: translate(-50%, -50%) scale(1.5); opacity: 0.3; }
  100% { transform: translate(-50%, -50%) scale(2); opacity: 0; }
}

@keyframes indicatorPulse {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.2); }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes iconGlow {
  0%, 100% { 
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3)) drop-shadow(0 0 8px rgba(74, 172, 254, 0.4));
    transform: scale(1);
  }
  50% { 
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3)) drop-shadow(0 0 15px rgba(74, 172, 254, 0.8));
    transform: scale(1.1);
  }
}

@keyframes statusPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes statusBlink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0.3; }
}

@keyframes eyeBlink {
  0%, 90%, 100% { transform: scaleY(1); }
  95% { transform: scaleY(0.1); }
}

@keyframes antennaPulse {
  0%, 100% { 
    box-shadow: 0 0 5px #4facfe;
    transform: translateX(-50%) scale(1);
  }
  50% { 
    box-shadow: 0 0 15px #4facfe;
    transform: translateX(-50%) scale(1.2);
  }
}

@keyframes messageFlow {
  0%, 100% { 
    opacity: 0.3;
    width: 30%;
  }
  50% { 
    opacity: 1;
    width: 100%;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .login-box {
    width: 90%;
    padding: 32px 24px;
  }
  
  .network-nodes {
    .node-group {
      .platform-node, .social-node {
        width: 50px;
        height: 50px;
        
        .modern-platform-icon, .modern-social-icon {
          width: 40px;
          height: 40px;
          
          .platform-svg {
            width: 24px;
            height: 24px;
            
            .platform-text {
              font-size: 6px;
            }
          }
        }
      }
    }
    
    .ai-center .ai-brain {
      width: 60px;
      height: 60px;
      
      .ai-core {
        width: 50px;
        height: 50px;
        
        .ai-service-icon {
          width: 30px;
          height: 30px;
        }
      }
    }
  }
  
  .glassmorphism-container {
    display: none;
  }
}
</style> 