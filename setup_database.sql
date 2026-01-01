-- =============================================
-- MOVIERECOMM™ - MSSQL Server Database Setup
-- SQL Server 2020 Compatible
-- =============================================

-- Step 1: Create Database
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'MovieRecommDB')
BEGIN
    CREATE DATABASE MovieRecommDB;
    PRINT 'Database MovieRecommDB created successfully.';
END
ELSE
BEGIN
    PRINT 'Database MovieRecommDB already exists.';
END
GO

-- Use the database
USE MovieRecommDB;
GO

-- =============================================
-- Step 2: Create Users Table
-- =============================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Users]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Users] (
        [user_id] INT IDENTITY(1,1) PRIMARY KEY,
        [username] VARCHAR(50) NOT NULL UNIQUE,
        [email] VARCHAR(100) NOT NULL UNIQUE,
        [password_hash] VARCHAR(255) NOT NULL,
        [created_at] DATETIME DEFAULT GETDATE(),
        [last_login] DATETIME NULL,
        [is_active] BIT DEFAULT 1
    );
    
    -- Create indexes for better performance
    CREATE INDEX IX_Users_Username ON [dbo].[Users](username);
    CREATE INDEX IX_Users_Email ON [dbo].[Users](email);
    
    PRINT 'Users table created successfully.';
END
ELSE
BEGIN
    PRINT 'Users table already exists.';
END
GO

-- =============================================
-- Step 3: Create UserPreferences Table
-- =============================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[UserPreferences]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[UserPreferences] (
        [pref_id] INT IDENTITY(1,1) PRIMARY KEY,
        [user_id] INT NOT NULL,
        [movie_title] VARCHAR(500),
        [movie_id] VARCHAR(50) NULL,
        [rating] FLOAT NULL,
        [watched_date] DATETIME DEFAULT GETDATE(),
        [is_favorite] BIT DEFAULT 0,
        CONSTRAINT FK_UserPreferences_Users FOREIGN KEY ([user_id]) 
            REFERENCES [dbo].[Users]([user_id]) ON DELETE CASCADE
    );
    
    -- Create index for better query performance
    CREATE INDEX IX_UserPreferences_UserId ON [dbo].[UserPreferences](user_id);
    CREATE INDEX IX_UserPreferences_MovieTitle ON [dbo].[UserPreferences](movie_title);
    
    PRINT 'UserPreferences table created successfully.';
END
ELSE
BEGIN
    PRINT 'UserPreferences table already exists.';
END
GO

-- =============================================
-- Step 4: Create Watchlist Table
-- =============================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Watchlist]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Watchlist] (
        [watchlist_id] INT IDENTITY(1,1) PRIMARY KEY,
        [user_id] INT NOT NULL,
        [movie_title] VARCHAR(500) NOT NULL,
        [movie_id] VARCHAR(50) NULL,
        [added_date] DATETIME DEFAULT GETDATE(),
        [watched] BIT DEFAULT 0,
        CONSTRAINT FK_Watchlist_Users FOREIGN KEY ([user_id]) 
            REFERENCES [dbo].[Users]([user_id]) ON DELETE CASCADE
    );
    
    CREATE INDEX IX_Watchlist_UserId ON [dbo].[Watchlist](user_id);
    
    PRINT 'Watchlist table created successfully.';
END
ELSE
BEGIN
    PRINT 'Watchlist table already exists.';
END
GO

-- =============================================
-- Step 5: Create UserActivity Table (for tracking)
-- =============================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[UserActivity]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[UserActivity] (
        [activity_id] INT IDENTITY(1,1) PRIMARY KEY,
        [user_id] INT NOT NULL,
        [activity_type] VARCHAR(50) NOT NULL, -- 'search', 'view', 'rate', 'favorite'
        [movie_title] VARCHAR(500) NULL,
        [activity_date] DATETIME DEFAULT GETDATE(),
        CONSTRAINT FK_UserActivity_Users FOREIGN KEY ([user_id]) 
            REFERENCES [dbo].[Users]([user_id]) ON DELETE CASCADE
    );
    
    CREATE INDEX IX_UserActivity_UserId ON [dbo].[UserActivity](user_id);
    CREATE INDEX IX_UserActivity_Date ON [dbo].[UserActivity](activity_date);
    
    PRINT 'UserActivity table created successfully.';
END
ELSE
BEGIN
    PRINT 'UserActivity table already exists.';
END
GO

-- =============================================
-- Step 6: Create Stored Procedures
-- =============================================

-- Procedure to Register New User
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[sp_RegisterUser]') AND type in (N'P'))
    DROP PROCEDURE [dbo].[sp_RegisterUser];
GO

CREATE PROCEDURE [dbo].[sp_RegisterUser]
    @username VARCHAR(50),
    @email VARCHAR(100),
    @password_hash VARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        -- Check if username or email already exists
        IF EXISTS (SELECT 1 FROM Users WHERE username = @username)
        BEGIN
            SELECT 'ERROR' AS Status, 'Username already exists' AS Message;
            RETURN;
        END
        
        IF EXISTS (SELECT 1 FROM Users WHERE email = @email)
        BEGIN
            SELECT 'ERROR' AS Status, 'Email already exists' AS Message;
            RETURN;
        END
        
        -- Insert new user
        INSERT INTO Users (username, email, password_hash)
        VALUES (@username, @email, @password_hash);
        
        SELECT 'SUCCESS' AS Status, 'User registered successfully' AS Message, SCOPE_IDENTITY() AS user_id;
    END TRY
    BEGIN CATCH
        SELECT 'ERROR' AS Status, ERROR_MESSAGE() AS Message;
    END CATCH
END
GO

-- Procedure to Authenticate User
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[sp_AuthenticateUser]') AND type in (N'P'))
    DROP PROCEDURE [dbo].[sp_AuthenticateUser];
GO

CREATE PROCEDURE [dbo].[sp_AuthenticateUser]
    @username VARCHAR(50),
    @password_hash VARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @user_id INT;
    
    SELECT @user_id = user_id
    FROM Users
    WHERE username = @username AND password_hash = @password_hash AND is_active = 1;
    
    IF @user_id IS NOT NULL
    BEGIN
        -- Update last login
        UPDATE Users SET last_login = GETDATE() WHERE user_id = @user_id;
        
        SELECT 'SUCCESS' AS Status, @user_id AS user_id, username, email
        FROM Users
        WHERE user_id = @user_id;
    END
    ELSE
    BEGIN
        SELECT 'ERROR' AS Status, 'Invalid credentials' AS Message;
    END
END
GO

-- Procedure to Add Movie to Preferences
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[sp_AddMoviePreference]') AND type in (N'P'))
    DROP PROCEDURE [dbo].[sp_AddMoviePreference];
GO

CREATE PROCEDURE [dbo].[sp_AddMoviePreference]
    @user_id INT,
    @movie_title VARCHAR(500),
    @rating FLOAT = NULL,
    @is_favorite BIT = 0
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        -- Check if preference already exists
        IF EXISTS (SELECT 1 FROM UserPreferences WHERE user_id = @user_id AND movie_title = @movie_title)
        BEGIN
            -- Update existing preference
            UPDATE UserPreferences
            SET rating = @rating, is_favorite = @is_favorite, watched_date = GETDATE()
            WHERE user_id = @user_id AND movie_title = @movie_title;
        END
        ELSE
        BEGIN
            -- Insert new preference
            INSERT INTO UserPreferences (user_id, movie_title, rating, is_favorite)
            VALUES (@user_id, @movie_title, @rating, @is_favorite);
        END
        
        SELECT 'SUCCESS' AS Status, 'Preference saved' AS Message;
    END TRY
    BEGIN CATCH
        SELECT 'ERROR' AS Status, ERROR_MESSAGE() AS Message;
    END CATCH
END
GO

-- Procedure to Get User Preferences
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[sp_GetUserPreferences]') AND type in (N'P'))
    DROP PROCEDURE [dbo].[sp_GetUserPreferences];
GO

CREATE PROCEDURE [dbo].[sp_GetUserPreferences]
    @user_id INT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        pref_id,
        movie_title,
        rating,
        watched_date,
        is_favorite
    FROM UserPreferences
    WHERE user_id = @user_id
    ORDER BY watched_date DESC;
END
GO

-- =============================================
-- Step 7: Create Views for Easy Querying
-- =============================================

-- View for User Statistics
IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_UserStatistics')
    DROP VIEW vw_UserStatistics;
GO

CREATE VIEW vw_UserStatistics AS
SELECT 
    u.user_id,
    u.username,
    u.email,
    u.created_at,
    u.last_login,
    COUNT(DISTINCT up.pref_id) AS total_movies_watched,
    AVG(up.rating) AS average_rating,
    COUNT(DISTINCT w.watchlist_id) AS watchlist_count
FROM Users u
LEFT JOIN UserPreferences up ON u.user_id = up.user_id
LEFT JOIN Watchlist w ON u.user_id = w.user_id
GROUP BY u.user_id, u.username, u.email, u.created_at, u.last_login;
GO

-- =============================================
-- Step 8: Insert Sample Test Data (Optional)
-- =============================================

-- You can uncomment this to insert test data
/*
-- Test User (password: test123 - SHA256 hashed)
INSERT INTO Users (username, email, password_hash)
VALUES ('testuser', 'test@example.com', 'ecd71870d1963316a97e3ac3408c9835ad8cf0f3c1bc703527c30265534f75ae');

-- Test Preferences
DECLARE @test_user_id INT = (SELECT user_id FROM Users WHERE username = 'testuser');

INSERT INTO UserPreferences (user_id, movie_title, rating, is_favorite)
VALUES 
    (@test_user_id, 'The Shawshank Redemption', 9.5, 1),
    (@test_user_id, 'The Godfather', 9.0, 1),
    (@test_user_id, 'The Dark Knight', 8.8, 0);
*/

-- =============================================
-- Step 9: Grant Permissions (Adjust as needed)
-- =============================================

-- Create a specific login for the application
-- Uncomment and modify with your desired credentials
/*
USE master;
GO

IF NOT EXISTS (SELECT * FROM sys.server_principals WHERE name = 'movieapp_user')
BEGIN
    CREATE LOGIN movieapp_user WITH PASSWORD = 'YourStrongPassword123!';
    PRINT 'Login movieapp_user created.';
END
GO

USE MovieRecommDB;
GO

IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'movieapp_user')
BEGIN
    CREATE USER movieapp_user FOR LOGIN movieapp_user;
    PRINT 'User movieapp_user created in MovieRecommDB.';
END
GO

-- Grant permissions
ALTER ROLE db_datareader ADD MEMBER movieapp_user;
ALTER ROLE db_datawriter ADD MEMBER movieapp_user;
GRANT EXECUTE TO movieapp_user;
GO

PRINT 'Permissions granted to movieapp_user.';
*/

-- =============================================
-- Verification Queries
-- =============================================

PRINT '============================================='
PRINT 'Database Setup Complete!'
PRINT '============================================='
PRINT ''
PRINT 'Created Tables:'
SELECT name AS TableName, create_date AS CreatedDate
FROM sys.tables
WHERE name IN ('Users', 'UserPreferences', 'Watchlist', 'UserActivity')
ORDER BY name;

PRINT ''
PRINT 'Created Stored Procedures:'
SELECT name AS ProcedureName, create_date AS CreatedDate
FROM sys.procedures
WHERE name LIKE 'sp_%'
ORDER BY name;

PRINT ''
PRINT 'Created Views:'
SELECT name AS ViewName, create_date AS CreatedDate
FROM sys.views
WHERE name LIKE 'vw_%'
ORDER BY name;

PRINT ''
PRINT '============================================='
PRINT 'Setup completed successfully!'
PRINT 'You can now run your Flask application.'
PRINT '============================================='
GO