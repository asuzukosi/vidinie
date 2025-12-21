twimport { MongoClient, Db, MongoClientOptions } from "mongodb";

const MONGODB_URI = process.env.DATABASE;
const MONGODB_DB = process.env.DB_NAME || "mydatabase";

//Global namespace defaults.
declare global {
  var _mongoClientPromise: Promise<MongoClient>;
}
if (!MONGODB_URI) {
  throw new Error("Mongo_URI is not found. Please put it in the enviroment.");
} else {
  console.log("MongoDB URI found.");
}
const options: MongoClientOptions = {
  maxPoolSize: 10,
  minPoolSize: 5,
  maxIdleTimeMS: 30000,
  serverSelectionTimeoutMS: 5000,
  socketTimeoutMS: 45000,
};
let client: MongoClient;
let clientPromise: Promise<MongoClient>;

if (process.env.NODE_ENV === "development") {
  if (!global._mongoClientPromise) {
    client = new MongoClient(MONGODB_URI, options);
    global._mongoClientPromise = client.connect();
  }
  clientPromise = global._mongoClientPromise;
} else {
  client = new MongoClient(MONGODB_URI, options);
  clientPromise = client.connect();
}

/**
 * Get the MongoDB client instance
 * @returns Promise that resolves to MongoClient
 */
export async function getMongoClient(): Promise<MongoClient> {
  return clientPromise;
}

/**
 * Get the MongoDB database instance
 * @returns Promise that resolves to Db
 */
export async function getDatabase(): Promise<Db> {
  const client = await getMongoClient();
  return client.db(MONGODB_DB);
}
/**
 * Close the MongoDB client connection
 */
export async function closeMongoClient(): Promise<void> {
  try {
    const client = await getMongoClient();
    await client.close();
    console.log("MongoDB connection closed");
  } catch (error) {
    console.error("Error closing MongoDB connection:", error);
    throw error;
  }
}
