// 全局布局修复 - 彻底消除空白
(function() {
  console.log('🔧 全局布局修复启动...');

  function injectGlobalFix() {
    // 创建并注入全局CSS
    const style = document.createElement('style');
    style.textContent = `
      /* 全局重置 - 消除所有可能的空白 */
      * {
        box-sizing: border-box !important;
      }

      body {
        margin: 0 !important;
        padding: 0 !important;
      }

      .app {
        margin: 0 !important;
        padding: 0 !important;
      }

      .main {
        margin-left: 210px !important;
        margin-top: 0 !important;
        margin-right: 0 !important;
        margin-bottom: 0 !important;
        padding: 0 !important;
      }

      .topbar {
        margin: 0 !important;
        padding: 0 24px !important;
        height: 50px !important;
      }

      .page-content {
        margin: 0 !important;
        padding: 20px 24px !important;
        width: 100% !important;
      }

      .page-section {
        margin: 0 !important;
        padding: 0 !important;
      }

      .page-section.active {
        margin: 0 !important;
        padding: 0 !important;
      }

      /* 修复特定页面布局 */
      .vein-layout,
      .chronicle-layout,
      .report3-layout {
        margin: 0 !important;
        padding: 0 !important;
      }

      .section-hd {
        margin-top: 0 !important;
        padding-top: 0 !important;
      }

      .hero {
        margin-top: 0 !important;
      }

      /* 确保内容从顶部开始 */
      #page-vein,
      #page-chronicle,
      #page-report3,
      #page-newproject,
      #page-overview,
      #page-import,
      #page-keyword,
      #page-busi,
      #page-dashboard,
      #page-model,
      #page-skill {
        margin-top: 0 !important;
        padding-top: 0 !important;
      }
    `;
    document.head.appendChild(style);
    console.log('✅ 全局CSS注入完成');
  }

  // 立即执行
  injectGlobalFix();

  console.log('🎉 全局布局修复完成！');
})();
