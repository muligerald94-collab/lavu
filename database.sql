-- Lavu Database SQL Setup
-- Run this in Supabase SQL Editor to create all required tables

-- ========================================
-- 1. USER SUBSCRIPTIONS TABLE
-- ========================================
CREATE TABLE IF NOT EXISTS user_subscriptions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  plan_id TEXT NOT NULL,
  plan_name TEXT NOT NULL,
  amount DECIMAL(10, 2) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_created_at ON user_subscriptions(created_at);

-- Enable RLS
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can view their own subscriptions
CREATE POLICY "Users can view their own subscriptions"
  ON user_subscriptions
  FOR SELECT
  USING (auth.uid() = user_id);

-- RLS Policy: Users can insert their own subscriptions
CREATE POLICY "Users can insert their own subscriptions"
  ON user_subscriptions
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can update their own subscriptions
CREATE POLICY "Users can update their own subscriptions"
  ON user_subscriptions
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- ========================================
-- 2. PAYMENTS TABLE
-- ========================================
CREATE TABLE IF NOT EXISTS payments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  transaction_id TEXT UNIQUE NOT NULL,
  amount DECIMAL(10, 2) NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  mpesa_receipt_number TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_transaction_id ON payments(transaction_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_created_at ON payments(created_at);

-- Enable RLS
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can view their own payments
CREATE POLICY "Users can view their own payments"
  ON payments
  FOR SELECT
  USING (auth.uid() = user_id);

-- RLS Policy: Users can insert their own payments
CREATE POLICY "Users can insert their own payments"
  ON payments
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can update their own payments (for status updates)
CREATE POLICY "Users can update their own payments"
  ON payments
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- ========================================
-- 3. PICKUPS TABLE
-- ========================================
CREATE TABLE IF NOT EXISTS pickups (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  pickup_date TIMESTAMP WITH TIME ZONE NOT NULL,
  notes TEXT,
  status TEXT NOT NULL DEFAULT 'scheduled',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_pickups_user_id ON pickups(user_id);
CREATE INDEX IF NOT EXISTS idx_pickups_status ON pickups(status);
CREATE INDEX IF NOT EXISTS idx_pickups_pickup_date ON pickups(pickup_date);
CREATE INDEX IF NOT EXISTS idx_pickups_created_at ON pickups(created_at);

-- Enable RLS
ALTER TABLE pickups ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can view their own pickups
CREATE POLICY "Users can view their own pickups"
  ON pickups
  FOR SELECT
  USING (auth.uid() = user_id);

-- RLS Policy: Users can insert their own pickups
CREATE POLICY "Users can insert their own pickups"
  ON pickups
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can update their own pickups
CREATE POLICY "Users can update their own pickups"
  ON pickups
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can delete their own pickups
CREATE POLICY "Users can delete their own pickups"
  ON pickups
  FOR DELETE
  USING (auth.uid() = user_id);

-- ========================================
-- 4. MPESA PAYMENT LOGS TABLE (Optional, for audit trail)
-- ========================================
CREATE TABLE IF NOT EXISTS mpesa_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  phone_number TEXT NOT NULL,
  amount DECIMAL(10, 2) NOT NULL,
  request_id TEXT,
  checkout_request_id TEXT UNIQUE,
  response_body JSONB,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_mpesa_logs_user_id ON mpesa_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_mpesa_logs_checkout_request_id ON mpesa_logs(checkout_request_id);
CREATE INDEX IF NOT EXISTS idx_mpesa_logs_created_at ON mpesa_logs(created_at);

-- Enable RLS
ALTER TABLE mpesa_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can view their own M-Pesa logs
CREATE POLICY "Users can view their own mpesa logs"
  ON mpesa_logs
  FOR SELECT
  USING (auth.uid() = user_id);

-- ========================================
-- 5. USER PROFILES TABLE (Extended user information)
-- ========================================
CREATE TABLE IF NOT EXISTS user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name TEXT,
  phone_number TEXT,
  email TEXT,
  address TEXT,
  city TEXT,
  postal_code TEXT,
  avatar_url TEXT,
  preferences JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- Enable RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can view their own profile
CREATE POLICY "Users can view their own profile"
  ON user_profiles
  FOR SELECT
  USING (auth.uid() = id);

-- RLS Policy: Users can update their own profile
CREATE POLICY "Users can update their own profile"
  ON user_profiles
  FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- RLS Policy: Users can insert their own profile
CREATE POLICY "Users can insert their own profile"
  ON user_profiles
  FOR INSERT
  WITH CHECK (auth.uid() = id);

-- ========================================
-- 6. PAYMENT HISTORY VIEW (For dashboard/history display)
-- ========================================

-- View: Complete payment history with calculated fields
CREATE OR REPLACE VIEW payment_history_view AS
SELECT 
  p.id,
  p.user_id,
  p.transaction_id,
  p.amount,
  p.status,
  p.mpesa_receipt_number,
  p.created_at,
  p.updated_at,
  DATE(p.created_at AT TIME ZONE 'Africa/Nairobi') as payment_date,
  EXTRACT(MONTH FROM p.created_at) as payment_month,
  EXTRACT(YEAR FROM p.created_at) as payment_year,
  CASE 
    WHEN p.status = 'completed' THEN 'Success'
    WHEN p.status = 'pending' THEN 'Pending'
    WHEN p.status = 'failed' THEN 'Failed'
    ELSE 'Unknown'
  END as status_label
FROM payments p
ORDER BY p.created_at DESC;

-- View: User's recent subscriptions
CREATE OR REPLACE VIEW user_subscriptions_view AS
SELECT 
  user_id,
  plan_id,
  plan_name,
  amount,
  created_at,
  ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) as row_num
FROM user_subscriptions;

-- View: User's payment summary
CREATE OR REPLACE VIEW user_payments_summary AS
SELECT 
  user_id,
  status,
  COUNT(*) as total_count,
  SUM(amount) as total_amount,
  MAX(created_at) as last_payment_date,
  DATE(MAX(created_at)) as last_payment_date_only
FROM payments
GROUP BY user_id, status;

-- View: Monthly payment statistics
CREATE OR REPLACE VIEW monthly_payment_stats AS
SELECT 
  user_id,
  EXTRACT(YEAR FROM created_at) as year,
  EXTRACT(MONTH FROM created_at) as month,
  COUNT(*) as transaction_count,
  SUM(amount) as total_amount,
  AVG(amount) as average_amount,
  MAX(amount) as max_amount,
  MIN(amount) as min_amount,
  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count,
  SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count
FROM payments
GROUP BY user_id, year, month
ORDER BY user_id, year DESC, month DESC;

-- ========================================
-- 7. FUNCTIONS FOR COMMON OPERATIONS
-- ========================================

-- Function: Get user's latest subscription
CREATE OR REPLACE FUNCTION get_user_latest_subscription(user_uuid UUID)
RETURNS TABLE (
  id UUID,
  plan_id TEXT,
  plan_name TEXT,
  amount DECIMAL,
  created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    user_subscriptions.id,
    user_subscriptions.plan_id,
    user_subscriptions.plan_name,
    user_subscriptions.amount,
    user_subscriptions.created_at
  FROM user_subscriptions
  WHERE user_subscriptions.user_id = user_uuid
  ORDER BY user_subscriptions.created_at DESC
  LIMIT 1;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function: Get user's total payments
CREATE OR REPLACE FUNCTION get_user_total_payments(user_uuid UUID)
RETURNS DECIMAL AS $$
DECLARE
  total DECIMAL;
BEGIN
  SELECT COALESCE(SUM(amount), 0) INTO total
  FROM payments
  WHERE user_id = user_uuid AND status = 'completed';
  RETURN total;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function: Get user's payment history with pagination
CREATE OR REPLACE FUNCTION get_user_payment_history(
  user_uuid UUID,
  limit_count INT DEFAULT 50,
  offset_count INT DEFAULT 0
)
RETURNS TABLE (
  id UUID,
  transaction_id TEXT,
  amount DECIMAL,
  status TEXT,
  mpesa_receipt_number TEXT,
  created_at TIMESTAMP WITH TIME ZONE,
  payment_date DATE,
  status_label TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    p.id,
    p.transaction_id,
    p.amount,
    p.status,
    p.mpesa_receipt_number,
    p.created_at,
    DATE(p.created_at AT TIME ZONE 'Africa/Nairobi'),
    CASE 
      WHEN p.status = 'completed' THEN 'Success'
      WHEN p.status = 'pending' THEN 'Pending'
      WHEN p.status = 'failed' THEN 'Failed'
      ELSE 'Unknown'
    END
  FROM payments p
  WHERE p.user_id = user_uuid
  ORDER BY p.created_at DESC
  LIMIT limit_count OFFSET offset_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function: Get user's payment statistics
CREATE OR REPLACE FUNCTION get_user_payment_stats(user_uuid UUID)
RETURNS TABLE (
  total_payments BIGINT,
  successful_payments BIGINT,
  failed_payments BIGINT,
  pending_payments BIGINT,
  total_amount DECIMAL,
  average_amount DECIMAL,
  last_payment_date TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    COUNT(*),
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END),
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END),
    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END),
    COALESCE(SUM(amount), 0),
    COALESCE(AVG(amount), 0),
    MAX(created_at)
  FROM payments
  WHERE user_id = user_uuid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ========================================
-- 8. TRIGGERS FOR AUTO-UPDATES
-- ========================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = TIMEZONE('utc'::text, NOW());
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for user_subscriptions
DROP TRIGGER IF EXISTS trigger_update_user_subscriptions_updated_at ON user_subscriptions;
CREATE TRIGGER trigger_update_user_subscriptions_updated_at
BEFORE UPDATE ON user_subscriptions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Trigger for payments
DROP TRIGGER IF EXISTS trigger_update_payments_updated_at ON payments;
CREATE TRIGGER trigger_update_payments_updated_at
BEFORE UPDATE ON payments
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Trigger for pickups
DROP TRIGGER IF EXISTS trigger_update_pickups_updated_at ON pickups;
CREATE TRIGGER trigger_update_pickups_updated_at
BEFORE UPDATE ON pickups
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Trigger for user_profiles
DROP TRIGGER IF EXISTS trigger_update_user_profiles_updated_at ON user_profiles;
CREATE TRIGGER trigger_update_user_profiles_updated_at
BEFORE UPDATE ON user_profiles
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- Setup Complete!
-- ========================================
-- All tables are now created with:
-- ✓ Proper indexing for performance
-- ✓ Row Level Security (RLS) enabled
-- ✓ Auto-update timestamps
-- ✓ Audit trails for M-Pesa
-- ✓ Useful views and functions
