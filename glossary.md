# 用語集

CV・人体姿勢推定・生成モデル分野の訳語．新しい論文で訳語を決めたら追記する．
「初出で英語を添える」の列が ✓ の語は，論文中の初出で「訳語（English）」と書く．

## 一般

| English | 訳語 | 初出で英語を添える |
|---|---|---|
| ablation study | アブレーション実験 | |
| baseline | ベースライン | |
| benchmark | ベンチマーク | |
| fine-tuning | ファインチューニング | |
| ground truth | 正解 | |
| in-domain / out-of-domain (OOD) | ドメイン内 / ドメイン外（OOD） | ✓ |
| cross-domain | クロスドメイン | |
| in-the-wild | in-the-wild（実環境の） | ✓ |
| state-of-the-art | 最先端の | |
| supervised / unsupervised / self-supervised | 教師あり / 教師なし / 自己教師あり | |
| supervision | 教師（教師信号） | |
| prior | 事前分布 / 事前知識 | |
| robust / robustness | 頑健な / 頑健性 | |
| plausible | 妥当な / 自然な | |
| generalization | 汎化 | |
| qualitative / quantitative | 定性的 / 定量的 | |
| metric | 評価指標 | |
| hyperparameter | ハイパーパラメータ | |
| learning rate | 学習率 | |
| iteration | 反復 | |
| optimizer | オプティマイザ | |
| loss | 損失 | |
| regularize | 正則化する | |

## 幾何・カメラ

| English | 訳語 | 初出で英語を添える |
|---|---|---|
| triangulation | 三角測量 | |
| reprojection / reprojection error | 再投影 / 再投影誤差 | |
| perspective projection | 透視投影 | |
| orthographic projection | 正射影 | |
| pinhole camera model | ピンホールカメラモデル | |
| viewpoint / view | 視点 | |
| multi-view | 多視点 | |
| monocular | 単眼 | |
| depth ambiguity | 奥行きの曖昧性 | |
| scale ambiguity | スケールの曖昧性 | |
| elevation / azimuth | 仰角 / 方位角 | |
| calibration | 較正 | |
| extrinsics / intrinsics | 外部パラメータ / 内部パラメータ | |

## 人体姿勢

| English | 訳語 | 初出で英語を添える |
|---|---|---|
| 3D human pose estimation | 3D人体姿勢推定 | |
| 2D-3D lifting | 2D-3Dリフティング | |
| keypoint / joint | キーポイント / 関節 | |
| bone length | 骨長 | |
| self-occlusion | 自己遮蔽 | |
| occlusion | 遮蔽 | |
| joint articulation | 関節の曲がり方 | |
| anatomical constraint | 解剖学的制約 | |
| mesh recovery | メッシュ復元 | |
| motion capture | モーションキャプチャ | |
| MPJPE (mean per-joint position error) | 平均関節位置誤差（MPJPE） | ✓ |
| end-to-end | end-to-end | |

## 生成モデル

| English | 訳語 | 初出で英語を添える |
|---|---|---|
| diffusion model | 拡散モデル | |
| motion diffusion model (MDM) | モーション拡散モデル（MDM） | ✓ |
| diffusion prior | 拡散事前分布 | |
| denoising (step) | ノイズ除去（ステップ） | |
| ancestral sampling | 祖先サンプリング | ✓ |
| noise schedule | ノイズスケジュール | |
| posterior | 事後分布 | |
| manifold | 多様体 | |
| unconditional / conditional generation | 無条件生成 / 条件付き生成 | |
| guidance | ガイダンス | |
| normalizing flow | 正規化フロー | |
| adversarial training | 敵対的学習 | |
| variational autoencoder (VAE) | 変分オートエンコーダ（VAE） | |
| latent | 潜在 | |
| fidelity | 忠実度 | |
