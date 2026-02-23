export interface RecommendedChannel {
  id: string;
  title: string;
  desc: string;
  badge: string;
  bg: string;
}

export interface LiveHomeShoppingChannel {
  id: string;
  channelName: string;
  currentProgram: string;
  bg: string;
}

export interface Product {
  id: string;
  name: string;
  price: number;
}

export interface MockData {
  menus: string[];
  recommendedChannels: RecommendedChannel[];
  liveHomeShoppingChannels: LiveHomeShoppingChannel[];
  products: Product[];
}
