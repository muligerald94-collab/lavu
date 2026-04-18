# Lavu Admin Dashboard

The admin dashboard is a web-based interface for managing orders and viewing subscriber analytics.

## Features

### 📦 Orders Management
- View all active orders (status: pending, picked up, in transit)
- See order details: customer, pickup/delivery addresses, scheduled date, weight, notes
- Update order status with a single click
- Real-time order status tracking
- Color-coded status indicators

### 📊 Analytics
- Total active subscribers
- Monthly KG usage statistics
- Subscriber usage breakdown by plan tier
- Individual subscriber usage percentages
- Plan adherence tracking

## Getting Started

### 1. Start the Backend
Make sure your Python backend is running:

```bash
# From the project root
python main.py
```

The backend should be running on `http://localhost:8000`

### 2. Open the Admin Dashboard
Open `admin_dashboard.html` in your web browser:
- **File path:** `c:\Users\user\Desktop\Lavu\admin_dashboard.html`
- Simply double-click the file or open it with your browser

### 3. Login
- **Password:** `lavu_admin_2024`
- Click "Login"

## Usage

### Managing Orders

1. Go to the **📦 Orders** tab
2. View all active orders with their current status
3. To update an order:
   - Select a new status from the dropdown
   - The order status updates automatically
   - A success message confirms the change
4. Statuses available:
   - **PENDING** - Order created, awaiting pickup
   - **PICKED_UP** - Items picked up from customer
   - **IN_TRANSIT** - Laundry being processed
   - **DELIVERED** - Order completed and delivered

### Viewing Analytics

1. Go to the **📊 Analytics** tab
2. See high-level statistics:
   - Active subscriber count
   - Total KG used this month
   - Total KG limit across all subscribers
   - Average usage percentage
3. Scroll down to see individual subscriber details:
   - Customer name and phone
   - Plan tier
   - Current month's usage vs limit
   - Usage percentage with visual progress bar
   - Red indicator if usage is >80% of limit

## API Endpoints Used

The dashboard connects to these backend endpoints:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/admin/orders` | Fetch all active orders |
| PUT | `/api/admin/orders/{order_id}` | Update order status |
| GET | `/api/admin/analytics` | Fetch subscriber analytics |

## Configuration

### Changing the Backend URL
If your backend is running on a different URL, edit the `admin_dashboard.html` file:

```javascript
const API_BASE_URL = 'http://localhost:8000'; // Change this line
```

### Changing the Admin Password
To set a different admin password, edit the same file:

```javascript
const ADMIN_PASSWORD = 'lavu_admin_2024'; // Change this line
```

## Security Notes

⚠️ **Important for Production:**

1. **Use JWT Authentication** - Replace simple password with proper JWT tokens
2. **HTTPS Only** - Always use HTTPS in production
3. **CORS Configuration** - Configure proper CORS headers in your backend:
   ```python
   from fastapi.middleware.cors import CORSMiddleware
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

4. **Rate Limiting** - Implement rate limiting on admin endpoints
5. **Audit Logging** - Log all admin actions for compliance

## Troubleshooting

### "Failed to load orders" error
- ✅ Ensure backend is running on `http://localhost:8000`
- ✅ Check that `main.py` doesn't have errors
- ✅ Verify CORS is enabled in the backend

### "Invalid password" error
- ✅ Check the password matches `ADMIN_PASSWORD` in the HTML file
- ✅ Default password: `lavu_admin_2024`

### No orders showing
- ✅ Check if there are active orders in the database
- ✅ Try refreshing the page
- ✅ Check backend logs for errors

### Orders not updating
- ✅ Ensure the backend PUT endpoint `/api/admin/orders/{order_id}` is working
- ✅ Check browser console for error messages (F12 → Console tab)

## Deployment

### Deploy to Web Server
You can deploy the admin dashboard to any web server:

```bash
# Copy the file to your server
scp admin_dashboard.html user@server.com:/var/www/html/

# Update the API_BASE_URL to point to your backend URL
# Edit the HTML file and change:
# const API_BASE_URL = 'https://api.example.com';
```

### Using with Render Backend
If your backend is deployed on Render:

```javascript
const API_BASE_URL = 'https://your-app-name.onrender.com';
```

## Future Enhancements

Potential features to add:

- [ ] Export analytics as CSV/PDF
- [ ] Real-time order notifications
- [ ] Admin user management
- [ ] Order search and filtering
- [ ] Pickup/delivery scheduling UI
- [ ] Payment reconciliation dashboard
- [ ] Dark mode
- [ ] Mobile-responsive admin app

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review backend logs for error details
3. Check browser console (F12) for JavaScript errors
