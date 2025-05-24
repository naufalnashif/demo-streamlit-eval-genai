import streamlit as st
from io import BytesIO
import requests
import utils.myFunc as mf 

def main():
    st.set_page_config(layout="wide")
    st.title("📊 AI Model Evaluation Dashboard")

    analyzer = mf.ExcelAnalyzer()

    # ------------------------ SIDEBAR ----------------------------
    st.sidebar.image("src/assets/ojk-logo-jpg.jpg")
    with st.sidebar:
        st.subheader('Settings :')
        with st.expander("General Settings :"):

            # Pilih sumber data
            data_source = st.radio(
                "Pilih sumber data:",
                options=["Upload File", "Gunakan Demo Dummy Data"],
                index=0
            )

            input_files = None  # Gunakan ini sebagai pengganti uploaded_files

            if data_source == "Upload File":
                uploaded_files = st.file_uploader(
                    "Unggah berkas XLSX",
                    type=['xlsx'], accept_multiple_files=True
                )
                if uploaded_files:
                    input_files = uploaded_files
                st.info("Silakan upload minimal satu file Excel (.xlsx).")

            else:  # Gunakan demo dummy dari huggingface
                demo_url = "https://huggingface.co/datasets/naufalnashif/assets-rfojk/resolve/main/RFOJK20250524_df_joined_demo.xlsx"
                try:
                    response = requests.get(demo_url)
                    demo_file = BytesIO(response.content)
                    demo_file.name = "RFOJK20250524_df_joined_demo.xlsx"
                    input_files = [demo_file]  # agar serupa dengan uploaded_files
                    st.success("Demo data berhasil dimuat.")
                except Exception as e:
                    st.error(f"Gagal memuat demo data: {e}")

    # ---------------------- VIDEO SECTION ------------------------
    if not input_files:
        st.video(
            "https://huggingface.co/datasets/naufalnashif/assets-rfojk/resolve/main/video-streamlit-demo-compress.mp4",
            format="video/mp4",
            loop=True,
            autoplay=True,
            muted=True
        )
        st.stop()

    # ------------------- PROSES DATASET -------------------------
    sheets = analyzer.get_all_sheet_names(input_files)
    if not sheets:
        st.warning("Tidak ada sheet ditemukan di file yang diupload.")
        return

    default_sheet = "Sheet1"
    sheet_choice = default_sheet if default_sheet in sheets else sheets[0]

    combined_df = analyzer.load_and_concat_sheets(input_files, sheet_choice)
    if combined_df is None or combined_df.empty:
        st.warning("Data gabungan kosong atau gagal dibaca.")
        return

    analyzer.df = combined_df

    num_cols, cat_cols = analyzer.get_columns()

    if len(cat_cols) == 0:
        st.warning("Data gabungan tidak memiliki kolom kategorikal untuk analisis.")
        return

    if analyzer.verif_col not in analyzer.df.columns:
        st.warning(f"Kolom '{analyzer.verif_col}' tidak ditemukan di data gabungan.")
        return

    verif_options = analyzer.df[analyzer.verif_col].dropna().unique().tolist()
    key_options = analyzer.df[analyzer.key_col].dropna().unique().tolist()
    type_options = analyzer.df[analyzer.type_col].dropna().unique().tolist()

    tab1, tab2, tab3 = st.tabs(["📈 AI Model Eval", "📊 Analytics", "📚 Doc"])

    with tab1:
        st.header("Summary :")
        df_counts, df_metrics, df_counts_total, df_metrics_total = analyzer.calculate_confusion_stats()
        if df_counts is None or df_metrics is None:
            st.warning("Data tidak mencukupi untuk menghitung statistik (pastikan kolom berisi 'True Positive', 'True Negative', 'False Positive', 'False Negative').")
        else:
            with st.expander ("Coef Matrix:"):
                # st.subheader("Coef Matrix Per Key")
                st.dataframe(
                    df_counts.style
                        .format({"Count": "{:,.0f}"})
                        .highlight_max(
                            subset=["TP", "FP", "FN", "TN", "Total"],
                            axis=0,
                            props='background-color: #ffdd57; color: black;'
                        ))

                st.dataframe(df_counts_total.style.format({"Count": "{:,.0f}"}))
            with st.expander ("Metrics:"):
                # st.subheader("Metrics Evaluasi Per Key")
                import pandas as pd
                # Format ke persen dan warnai berdasarkan threshold
                def highlight_metric(val):
                    if pd.isna(val):
                        return ''
                    elif val >= 0.8:
                        # return 'background-color: #bfff00; color: black;'  # hijau muda
                        return ''
                    else:
                        return 'background-color: #e97451; color: white;'  # merah kecoklatan

                # Format ke persen
                def fmt(val):
                    return f"{val:.2%}" if pd.notna(val) else "-"

                # Kolom yang ingin diformat & highlight
                highlight_cols = ["Accuracy", "Specificity", "Recall", "Precision", "F1 Score"]

                # Terapkan di Streamlit
                st.dataframe(
                    df_metrics.style
                        .format({col: fmt for col in highlight_cols})
                        .applymap(highlight_metric, subset=highlight_cols)
                )
                st.dataframe(df_metrics_total.style.format({col: fmt for col in highlight_cols}))

    with tab2:
        st.header("Bar Chart")
        with st.sidebar :
            with st.expander("Analytics Settings:"):
                # Tambahkan opsi 'All' di awal
                key_options_with_all = ['All'] + key_options
                type_options_with_all = ['All'] + type_options

                # Multiselect dengan default 'All'
                selected_key_raw = st.multiselect(
                    "Pilih Key:",
                    options=key_options_with_all,
                    default=['All']
                )

                selected_type_raw = st.selectbox(
                    "Pilih Type:",
                    options=type_options_with_all,
                    index=type_options_with_all.index('All') if 'All' in type_options_with_all else 0
                )

                # Batasi pilihan hanya ke kolom yang kamu mau
                allowed_cat_cols = ['Key', 'Type', 'Bab', 'Emiten']
                cat_cols_filtered = [col for col in cat_cols if col in allowed_cat_cols]

                analyzer.category_col = st.selectbox("Pilih Kolom Kategori Y-Bar", cat_cols_filtered)

                # Logika: jika 'All' dipilih, maka ambil semua opsi asli
                analyzer.selected_key = key_options if 'All' in selected_key_raw else selected_key_raw
                # analyzer.selected_type = type_options if 'All' in selected_type_raw else selected_type_raw
                analyzer.selected_type = type_options if selected_type_raw == 'All' else [selected_type_raw]

                analyzer.selected_verif = st.multiselect(
                    f"Pilih X-Bar '{analyzer.verif_col}'",
                    options=verif_options,
                    default=verif_options[:1]
                )

                analyzer.top_n = st.slider("Tentukan Top N: ", min_value=1, max_value=100, value=10)

                grouped, grouped_detail, grouped_with_criteria = analyzer.filter_and_group()
                
        if grouped.empty:
            st.info("Data tidak ditemukan untuk filter yang dipilih.")
        else:
            analyzer.plot_bar(grouped)
            with st.expander(f"### 📋 Tabel Detail {analyzer.category_col}:"):
                st.dataframe(grouped_detail)

            with st.expander(f"### 📋 Tabel Detail {analyzer.category_col} and Refinement Parameter:"):
                df = grouped_with_criteria.copy()

                # Filter berdasarkan analyzer.category_col (selectbox dengan opsi 'All')
                category_col = analyzer.category_col
                if category_col in df.columns:
                    category_values = sorted(df[category_col].dropna().unique().tolist())
                    category_options = ['All'] + category_values
                    selected_value = st.selectbox(f"Filter {category_col}:", category_options)

                    if selected_value != 'All':
                        df = df[df[category_col] == selected_value]

                # Tampilkan dataframe yang telah difilter
                st.dataframe(df, use_container_width=True)

    with tab3:
        st.subheader("📘 Documentation")
        st.markdown("""
        ### 🚀 Getting Started

        Welcome to the AI Evaluation Dashboard! Here's how to use it:

        1. **Upload** an Excel (.xlsx) file using the sidebar.
        2. **Choose** the category column (e.g., verification result).
        3. Head over to the **Statistics** tab to see counts and evaluation metrics (Accuracy, F1 Score, etc.).
        4. Use the **Data Analysis** tab to explore visualizations and filter data by multiple verification types.
        5. This **Documentation** tab is here to guide you whenever you need help.

        ---

        ### 🧠 App Architecture

        - **Backend**: Data processing with `Pandas`.
        - **Visualization**: Powered by `Matplotlib` and `Seaborn`.
        - **User Interface**: Built with `Streamlit` and organized via tab navigation.

        ---

        ### 🙌 Credits & Acknowledgements

        - Created by **Naufal Nashif**
        - Built with: `Pandas`, `Streamlit`, `Matplotlib`, `Seaborn`
        - Special thanks to the open-source community and official documentation for continuous inspiration ✨

        ---

        ### 🔗 Source Code & Docs

        Full source code and technical documentation available on GitHub:

        ```
        https://github.com/naufalnashif/rfojk-sreamlit-ai-eval
        ```

        Feel free to ⭐ the repo, fork it, or contribute!

        ---
        """)


if __name__ == "__main__":
    main()
