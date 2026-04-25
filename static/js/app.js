function app() {
  return {
    step: 1,
    steps: ['コンセプト', 'キーワード', '商品選択', '価格設定', '出品'],
    loading: false,

    form: {
      concept: '',
      category: '子供服',
    },

    research: {},
    selectedKeyword: '',
    products: [],
    selectedProducts: [],

    async doResearch() {
      this.loading = true;
      try {
        const res = await fetch('/api/research', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ concept: this.form.concept, category: this.form.category }),
        });
        this.research = await res.json();
        this.selectedKeyword = this.research.keywords?.[0] || '';
        this.step = 2;
      } catch (e) {
        alert('リサーチに失敗しました。APIキーを確認してください。');
      } finally {
        this.loading = false;
      }
    },

    async doSearch() {
      this.loading = true;
      try {
        const res = await fetch('/api/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ keyword: this.selectedKeyword, category: this.form.category }),
        });
        const data = await res.json();
        this.products = data.products;
        this.selectedProducts = [];
        this.step = 3;
      } catch (e) {
        alert('商品検索に失敗しました。');
      } finally {
        this.loading = false;
      }
    },

    toggleSelect(product) {
      const idx = this.selectedProducts.findIndex(p => p.id === product.id);
      if (idx >= 0) {
        this.selectedProducts.splice(idx, 1);
      } else {
        this.selectedProducts.push({ ...product, sell_price: product.suggested_price || '' });
      }
    },

    isSelected(product) {
      return this.selectedProducts.some(p => p.id === product.id);
    },

    allPricesSet() {
      return this.selectedProducts.length > 0 &&
        this.selectedProducts.every(p => p.sell_price && Number(p.sell_price) > 0);
    },

    async publishToBase(product) {
      product.base_status = 'loading';
      try {
        const res = await fetch('/api/publish', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            product_id: product.id,
            title: product.title,
            description: product.description,
            price: Number(product.sell_price),
            image_url: product.image_url,
            platform: 'base',
          }),
        });
        const data = await res.json();
        if (data.base?.status === 'success') {
          product.base_status = 'success';
          product.base_admin_url = data.base.admin_url;
        } else {
          product.base_status = 'error';
          product.base_error = data.base?.message || '出品に失敗しました';
        }
      } catch (e) {
        product.base_status = 'error';
        product.base_error = 'ネットワークエラーが発生しました';
      }
    },

    reset() {
      this.step = 1;
      this.form = { concept: '', category: '子供服' };
      this.research = {};
      this.selectedKeyword = '';
      this.products = [];
      this.selectedProducts = [];
    },
  };
}
