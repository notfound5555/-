HANEDA TAXI LIVE — 東京イベント情報・自動更新設定
=================================================

含まれるファイル
- index.html: サイト本体（既存カメラ・運賃表を含む）
- events.json: イベント関連の公式リンクと更新時刻
- scripts/update_events.py: リンクの到達確認と更新時刻の記録
- .github/workflows/update-events.yml: 毎日0:07 JSTのGitHub Actions設定

重要な注意
-----------
この版の自動処理は、公式イベント情報ページへのリンクが開けるかを確認し、
events.json の確認時刻を毎日更新するものです。イベント名・開催日・終演時刻を
各サイトから自動抽出して網羅する機能ではありません。各サイトの構造変更や
アクセス制限があるため、正確な全件自動収集には、提供元API/RSSなどの確認が必要です。

GitHubへの導入
--------------
1. ZIPを解凍します。
2. GitHubで公開サイトのリポジトリを開きます。
3. このフォルダ内のファイルをリポジトリ直下へ、フォルダ構成を維持して追加・置換します。
   .github/workflows/update-events.yml は .github/workflows/ 内に置いてください。
4. 変更をコミットします。
5. GitHubの Actions タブで "Update Tokyo event links" を開き、"Run workflow" で初回実行します。
6. GitHub Pagesのサイトを開き、イベント情報欄と更新時刻を確認します。

注意: GitHub Actionsの schedule はGitHub側の負荷などで遅れることがあります。
また、既存リポジトリのブランチ設定により、Pages公開対象ブランチと一致している必要があります。
