// AgTools Domain Models and Analytics
// F# Script for agricultural domain modeling, calculations, and analysis
// Builds upon pipeline.fsx for comprehensive farm management

#load "pipeline.fsx"

open System

// =============================================================================
// DOMAIN TYPES - Agricultural Entities
// =============================================================================

/// Crop types supported by the system
type CropType =
    | Corn
    | Soybean
    | Wheat
    | Rice
    | Cotton
    | Sorghum
    | Oats
    | Barley
    | Alfalfa
    | Custom of string

/// Soil texture classification
type SoilTexture =
    | Sand
    | LoamySand
    | SandyLoam
    | Loam
    | SiltLoam
    | Silt
    | SandyClayLoam
    | ClayLoam
    | SiltyClayLoam
    | SandyCite
    | SiltyClay
    | Clay

/// Soil test level categories
type SoilTestLevel =
    | VeryLow
    | Low
    | Medium
    | Optimum
    | High
    | VeryHigh

/// Tillage practice types
type TillagePractice =
    | ConventionalTill
    | ReducedTill
    | StripTill
    | NoTill
    | VerticalTill

/// Irrigation system types
type IrrigationSystem =
    | None
    | CenterPivot
    | LinearMove
    | DripTape
    | SubsurfaceDrip
    | Furrow
    | Flood

/// Field definition
type Field = {
    Id: Guid
    Name: string
    Acreage: float
    Crop: CropType
    SoilTexture: SoilTexture
    OrganicMatter: float
    Tillage: TillagePractice
    Irrigation: IrrigationSystem
    Latitude: float
    Longitude: float
    CountyFSA: string option
}

/// Equipment status
type EquipmentStatus =
    | Available
    | InUse
    | Maintenance
    | Repair
    | Retired

/// Equipment types
type EquipmentType =
    | Tractor
    | Combine
    | Sprayer
    | Planter
    | Drill
    | Tillage
    | Wagon
    | Truck
    | ATV
    | Drone
    | Other of string

/// Equipment definition
type Equipment = {
    Id: Guid
    Name: string
    EquipmentType: EquipmentType
    Make: string
    Model: string
    Year: int
    PurchasePrice: decimal
    CurrentHours: float
    Status: EquipmentStatus
    MaintenanceIntervalHours: float
    LastMaintenanceHours: float
}

// =============================================================================
// WEATHER AND CLIMATE TYPES
// =============================================================================

/// Weather conditions for spray timing
type WeatherConditions = {
    Temperature: float  // Fahrenheit
    WindSpeed: float    // MPH
    WindDirection: string
    Humidity: float     // Percentage
    DewPoint: float     // Fahrenheit
    ChanceOfRain: float // Percentage
    InversionRisk: bool
}

/// Spray condition rating
type SprayCondition =
    | Excellent
    | Good
    | Fair
    | Marginal
    | Poor
    | DoNotSpray

/// Growing Degree Day record
type GDDRecord = {
    Date: DateTime
    HighTemp: float
    LowTemp: float
    BaseTemp: float
    GDD: float
    AccumulatedGDD: float
}

/// Corn growth stages based on GDD
type CornGrowthStage =
    | VE    // Emergence
    | V1 | V2 | V3 | V4 | V5 | V6
    | V7 | V8 | V9 | V10 | V11 | V12
    | VT    // Tasseling
    | R1    // Silking
    | R2    // Blister
    | R3    // Milk
    | R4    // Dough
    | R5    // Dent
    | R6    // Maturity

/// Soybean growth stages
type SoybeanGrowthStage =
    | VE    // Emergence
    | VC    // Cotyledon
    | V1 | V2 | V3 | V4 | V5 | V6
    | R1    // Beginning bloom
    | R2    // Full bloom
    | R3    // Beginning pod
    | R4    // Full pod
    | R5    // Beginning seed
    | R6    // Full seed
    | R7    // Beginning maturity
    | R8    // Full maturity

// =============================================================================
// PEST AND DISEASE TYPES
// =============================================================================

/// Pest pressure levels
type PressureLevel =
    | None
    | Low
    | Moderate
    | High
    | Severe

/// Pest identification result
type PestIdentification = {
    PestName: string
    Confidence: float
    EconomicThreshold: float
    CurrentPressure: PressureLevel
    RecommendTreatment: bool
}

/// Disease identification result
type DiseaseIdentification = {
    DiseaseName: string
    Confidence: float
    Severity: PressureLevel
    FavorableConditions: bool
    RecommendTreatment: bool
}

/// Treatment recommendation
type TreatmentRecommendation = {
    ProductName: string
    ActiveIngredient: string
    RatePerAcre: float
    Unit: string
    CostPerAcre: decimal
    PreHarvestInterval: int  // Days
    RestrictedEntryInterval: float  // Hours
    ModeOfAction: string
}

// =============================================================================
// FINANCIAL TYPES
// =============================================================================

/// Expense categories
type ExpenseCategory =
    | Seed
    | Fertilizer
    | Chemical
    | Fuel
    | Labor
    | Equipment
    | LandRent
    | Insurance
    | Interest
    | Repairs
    | Custom
    | Hauling
    | Drying
    | Storage
    | Utilities
    | Miscellaneous

/// Expense record
type Expense = {
    Id: Guid
    Date: DateTime
    Category: ExpenseCategory
    Description: string
    Amount: decimal
    FieldAllocations: (Guid * float) list  // Field ID and percentage
    Vendor: string option
    InvoiceNumber: string option
}

/// Revenue record
type Revenue = {
    Id: Guid
    Date: DateTime
    Crop: CropType
    Bushels: float
    PricePerBushel: decimal
    TotalAmount: decimal
    Buyer: string
    FieldId: Guid
    ContractNumber: string option
}

/// Profitability analysis result
type ProfitabilityAnalysis = {
    FieldId: Guid
    FieldName: string
    Crop: CropType
    Acreage: float
    TotalRevenue: decimal
    TotalExpenses: decimal
    NetProfit: decimal
    ProfitPerAcre: decimal
    YieldPerAcre: float
    CostPerBushel: decimal
    BreakEvenYield: float
    BreakEvenPrice: decimal
    ROI: float
}

// =============================================================================
// CALCULATION FUNCTIONS
// =============================================================================

module Calculations =

    /// Calculate Growing Degree Days
    let calculateGDD (highTemp: float) (lowTemp: float) (baseTemp: float) : float =
        let avgTemp = (highTemp + lowTemp) / 2.0
        let cappedHigh = min highTemp 86.0  // Cap at 86°F for corn
        let cappedLow = max lowTemp baseTemp
        let cappedAvg = (cappedHigh + cappedLow) / 2.0
        max 0.0 (cappedAvg - baseTemp)

    /// Get base temperature for crop
    let getBaseTemp (crop: CropType) : float =
        match crop with
        | Corn -> 50.0
        | Soybean -> 50.0
        | Wheat -> 32.0
        | Rice -> 50.0
        | Cotton -> 60.0
        | Sorghum -> 50.0
        | Oats -> 32.0
        | Barley -> 32.0
        | Alfalfa -> 41.0
        | Custom _ -> 50.0

    /// Calculate accumulated GDD from a list of daily records
    let accumulateGDD (records: GDDRecord list) : float =
        records |> List.sumBy (fun r -> r.GDD)

    /// Predict corn growth stage from accumulated GDD
    let predictCornStage (accumulatedGDD: float) : CornGrowthStage =
        match accumulatedGDD with
        | gdd when gdd < 120.0 -> VE
        | gdd when gdd < 200.0 -> V1
        | gdd when gdd < 350.0 -> V2
        | gdd when gdd < 475.0 -> V3
        | gdd when gdd < 610.0 -> V6
        | gdd when gdd < 740.0 -> V9
        | gdd when gdd < 870.0 -> V12
        | gdd when gdd < 1135.0 -> VT
        | gdd when gdd < 1400.0 -> R1
        | gdd when gdd < 1660.0 -> R2
        | gdd when gdd < 1925.0 -> R3
        | gdd when gdd < 2190.0 -> R4
        | gdd when gdd < 2450.0 -> R5
        | _ -> R6

    /// Predict soybean growth stage from accumulated GDD
    let predictSoybeanStage (accumulatedGDD: float) : SoybeanGrowthStage =
        match accumulatedGDD with
        | gdd when gdd < 90.0 -> SoybeanGrowthStage.VE
        | gdd when gdd < 160.0 -> SoybeanGrowthStage.VC
        | gdd when gdd < 215.0 -> SoybeanGrowthStage.V1
        | gdd when gdd < 320.0 -> SoybeanGrowthStage.V3
        | gdd when gdd < 490.0 -> SoybeanGrowthStage.V5
        | gdd when gdd < 685.0 -> SoybeanGrowthStage.R1
        | gdd when gdd < 880.0 -> SoybeanGrowthStage.R2
        | gdd when gdd < 1080.0 -> SoybeanGrowthStage.R3
        | gdd when gdd < 1280.0 -> SoybeanGrowthStage.R4
        | gdd when gdd < 1480.0 -> SoybeanGrowthStage.R5
        | gdd when gdd < 1680.0 -> SoybeanGrowthStage.R6
        | gdd when gdd < 1880.0 -> SoybeanGrowthStage.R7
        | _ -> SoybeanGrowthStage.R8

    /// Evaluate spray conditions
    let evaluateSprayConditions (weather: WeatherConditions) : SprayCondition =
        let windScore =
            match weather.WindSpeed with
            | w when w < 3.0 -> 0   // Too calm, inversion risk
            | w when w < 5.0 -> 100
            | w when w < 10.0 -> 80
            | w when w < 15.0 -> 50
            | _ -> 0

        let tempScore =
            match weather.Temperature with
            | t when t < 40.0 -> 20
            | t when t < 50.0 -> 60
            | t when t >= 50.0 && t <= 85.0 -> 100
            | t when t < 90.0 -> 70
            | t when t < 95.0 -> 40
            | _ -> 10

        let humidityScore =
            match weather.Humidity with
            | h when h < 30.0 -> 40
            | h when h < 40.0 -> 70
            | h when h >= 40.0 && h <= 80.0 -> 100
            | h when h < 90.0 -> 70
            | _ -> 40

        let rainScore =
            match weather.ChanceOfRain with
            | r when r < 10.0 -> 100
            | r when r < 30.0 -> 80
            | r when r < 50.0 -> 50
            | r when r < 70.0 -> 20
            | _ -> 0

        let inversionPenalty = if weather.InversionRisk then -30 else 0

        let totalScore =
            (windScore + tempScore + humidityScore + rainScore) / 4 + inversionPenalty

        match totalScore with
        | s when s >= 90 -> Excellent
        | s when s >= 75 -> Good
        | s when s >= 60 -> Fair
        | s when s >= 45 -> Marginal
        | s when s >= 30 -> Poor
        | _ -> DoNotSpray

    /// Calculate break-even yield
    let calculateBreakEvenYield (totalCosts: decimal) (pricePerBushel: decimal) : float =
        if pricePerBushel > 0m then
            float (totalCosts / pricePerBushel)
        else
            0.0

    /// Calculate break-even price
    let calculateBreakEvenPrice (totalCosts: decimal) (totalBushels: float) : decimal =
        if totalBushels > 0.0 then
            totalCosts / decimal totalBushels
        else
            0m

    /// Calculate ROI percentage
    let calculateROI (revenue: decimal) (costs: decimal) : float =
        if costs > 0m then
            float ((revenue - costs) / costs) * 100.0
        else
            0.0

    /// Calculate cost per acre
    let calculateCostPerAcre (totalCosts: decimal) (acreage: float) : decimal =
        if acreage > 0.0 then
            totalCosts / decimal acreage
        else
            0m

    /// Calculate cost per bushel
    let calculateCostPerBushel (totalCosts: decimal) (totalBushels: float) : decimal =
        if totalBushels > 0.0 then
            totalCosts / decimal totalBushels
        else
            0m

// =============================================================================
// FERTILIZER OPTIMIZATION
// =============================================================================

module FertilizerOptimization =

    /// Nutrient types
    type Nutrient = Nitrogen | Phosphorus | Potassium | Sulfur | Zinc | Boron

    /// Fertilizer product
    type FertilizerProduct = {
        Name: string
        NitrogenContent: float    // Percentage
        PhosphorusContent: float  // P2O5 percentage
        PotassiumContent: float   // K2O percentage
        PricePerTon: decimal
    }

    /// Common fertilizer products
    let commonProducts = [
        { Name = "Urea (46-0-0)"; NitrogenContent = 46.0; PhosphorusContent = 0.0; PotassiumContent = 0.0; PricePerTon = 650m }
        { Name = "UAN 32%"; NitrogenContent = 32.0; PhosphorusContent = 0.0; PotassiumContent = 0.0; PricePerTon = 420m }
        { Name = "Anhydrous Ammonia (82-0-0)"; NitrogenContent = 82.0; PhosphorusContent = 0.0; PotassiumContent = 0.0; PricePerTon = 900m }
        { Name = "DAP (18-46-0)"; NitrogenContent = 18.0; PhosphorusContent = 46.0; PotassiumContent = 0.0; PricePerTon = 780m }
        { Name = "MAP (11-52-0)"; NitrogenContent = 11.0; PhosphorusContent = 52.0; PotassiumContent = 0.0; PricePerTon = 820m }
        { Name = "Potash (0-0-60)"; NitrogenContent = 0.0; PhosphorusContent = 0.0; PotassiumContent = 60.0; PricePerTon = 550m }
    ]

    /// Calculate cost per pound of nutrient
    let costPerPoundNutrient (product: FertilizerProduct) (nutrient: Nutrient) : decimal option =
        let content =
            match nutrient with
            | Nitrogen -> product.NitrogenContent
            | Phosphorus -> product.PhosphorusContent
            | Potassium -> product.PotassiumContent
            | _ -> 0.0

        if content > 0.0 then
            Some (product.PricePerTon / decimal (content * 20.0))  // 2000 lbs per ton, content is percentage
        else
            None

    /// Find cheapest nitrogen source
    let findCheapestNitrogen (products: FertilizerProduct list) : (FertilizerProduct * decimal) option =
        products
        |> List.choose (fun p ->
            costPerPoundNutrient p Nitrogen
            |> Option.map (fun cost -> (p, cost)))
        |> List.sortBy snd
        |> List.tryHead

    /// Calculate nitrogen rate based on yield goal
    let calculateNitrogenRate (yieldGoal: float) (crop: CropType) (soilOM: float) (previousCrop: CropType option) : float =
        let baseRate =
            match crop with
            | Corn -> yieldGoal * 1.2  // 1.2 lbs N per bushel yield goal
            | Wheat -> yieldGoal * 2.0
            | Sorghum -> yieldGoal * 1.0
            | Cotton -> yieldGoal * 0.06  // Per lb lint
            | _ -> 0.0

        // Credit for organic matter (approximately 20 lbs N per 1% OM above 2%)
        let omCredit = max 0.0 ((soilOM - 2.0) * 20.0)

        // Credit for previous legume crop
        let legumeCreditValue =
            match previousCrop with
            | Some Soybean -> 40.0
            | Some Alfalfa -> 100.0
            | _ -> 0.0

        max 0.0 (baseRate - omCredit - legumeCreditValue)

// =============================================================================
// YIELD RESPONSE AND ECONOMIC OPTIMUM RATE (EOR)
// =============================================================================

module YieldResponse =

    /// Yield response model types
    type ResponseModel =
        | Quadratic
        | QuadraticPlateau
        | LinearPlateau
        | Mitscherlich
        | SquareRoot

    /// Quadratic yield response: y = a + bx + cx²
    let quadraticResponse (a: float) (b: float) (c: float) (rate: float) : float =
        a + b * rate + c * rate * rate

    /// Calculate Economic Optimum Rate for quadratic model
    /// EOR = (b - Pn/Pc) / (-2c)
    /// where Pn = price of nutrient per lb, Pc = price of crop per unit
    let calculateEOR (b: float) (c: float) (nutrientPrice: float) (cropPrice: float) : float =
        if c <> 0.0 && cropPrice > 0.0 then
            (b - (nutrientPrice / cropPrice)) / (-2.0 * c)
        else
            0.0

    /// Calculate maximum yield rate (agronomic optimum)
    let calculateMaxYieldRate (b: float) (c: float) : float =
        if c <> 0.0 then
            -b / (2.0 * c)
        else
            0.0

    /// Generate yield response curve data points
    let generateResponseCurve (a: float) (b: float) (c: float) (maxRate: float) (steps: int) : (float * float) list =
        [ for i in 0 .. steps do
            let rate = float i * (maxRate / float steps)
            yield (rate, quadraticResponse a b c rate) ]

    /// Default corn nitrogen response parameters (typical Midwest)
    let defaultCornNitrogenParams = (50.0, 1.2, -0.004)  // (a, b, c)

    /// Calculate profit at a given rate
    let calculateProfit (yieldAtRate: float) (cropPrice: float) (nutrientRate: float) (nutrientPrice: float) : float =
        (yieldAtRate * cropPrice) - (nutrientRate * nutrientPrice)

    /// Compare multiple rates and return profitability
    let compareRates (rates: float list) (a: float) (b: float) (c: float) (cropPrice: float) (nutrientPrice: float) : (float * float * float) list =
        rates
        |> List.map (fun rate ->
            let yld = quadraticResponse a b c rate
            let profit = calculateProfit yld cropPrice rate nutrientPrice
            (rate, yld, profit))

// =============================================================================
// SUSTAINABILITY METRICS
// =============================================================================

module Sustainability =

    /// Carbon emission factors (kg CO2e per unit)
    type EmissionFactors = {
        DieselPerGallon: float      // kg CO2e per gallon
        GasolinePerGallon: float
        PropanePerGallon: float
        NaturalGasPerTherm: float
        ElectricityPerKWh: float
        NitrogenPerPound: float     // Embodied carbon in fertilizer
        PhosphorusPerPound: float
        PotassiumPerPound: float
    }

    /// Default emission factors (US averages)
    let defaultEmissionFactors = {
        DieselPerGallon = 10.21
        GasolinePerGallon = 8.89
        PropanePerGallon = 5.79
        NaturalGasPerTherm = 5.31
        ElectricityPerKWh = 0.42
        NitrogenPerPound = 2.5
        PhosphorusPerPound = 0.5
        PotassiumPerPound = 0.3
    }

    /// Carbon sequestration practices
    type SequestrationPractice =
        | NoTill of acreage: float
        | CoverCrops of acreage: float
        | ReducedTillage of acreage: float
        | Agroforestry of acreage: float
        | Wetlands of acreage: float

    /// Sequestration rates (kg CO2e per acre per year)
    let sequestrationRate (practice: SequestrationPractice) : float =
        match practice with
        | NoTill acres -> acres * 300.0
        | CoverCrops acres -> acres * 500.0
        | ReducedTillage acres -> acres * 150.0
        | Agroforestry acres -> acres * 1000.0
        | Wetlands acres -> acres * 800.0

    /// Calculate carbon footprint per acre
    let calculateCarbonFootprint
        (factors: EmissionFactors)
        (dieselGallons: float)
        (nitrogenLbs: float)
        (phosphorusLbs: float)
        (potassiumLbs: float)
        (acreage: float) : float =

        let totalEmissions =
            dieselGallons * factors.DieselPerGallon +
            nitrogenLbs * factors.NitrogenPerPound +
            phosphorusLbs * factors.PhosphorusPerPound +
            potassiumLbs * factors.PotassiumPerPound

        if acreage > 0.0 then totalEmissions / acreage else 0.0

    /// Sustainability score calculation (0-100)
    let calculateSustainabilityScore
        (carbonFootprintPerAcre: float)
        (waterEfficiency: float)  // gallons per bushel
        (pesticideReduction: float)  // percentage vs conventional
        (soilHealthIndex: float)  // 0-100
        : float =

        // Lower carbon is better (benchmark: 500 kg/acre)
        let carbonScore = max 0.0 (100.0 - (carbonFootprintPerAcre / 5.0))

        // Lower water use is better (benchmark: 20 gal/bu for corn)
        let waterScore = max 0.0 (100.0 - (waterEfficiency * 5.0))

        // Higher pesticide reduction is better
        let pesticideScore = pesticideReduction

        // Weighted average
        (carbonScore * 0.3 + waterScore * 0.2 + pesticideScore * 0.2 + soilHealthIndex * 0.3)

    /// Grade based on score
    let gradeFromScore (score: float) : string =
        match score with
        | s when s >= 90.0 -> "A"
        | s when s >= 80.0 -> "B"
        | s when s >= 70.0 -> "C"
        | s when s >= 60.0 -> "D"
        | _ -> "F"

// =============================================================================
// REPORT GENERATION
// =============================================================================

module Reports =

    /// Report format types
    type ReportFormat = PDF | Excel | CSV | JSON

    /// Report types available
    type ReportType =
        | FieldPerformance
        | CostAnalysis
        | ProfitabilityByField
        | ProfitabilityByCrop
        | InputUsage
        | Sustainability
        | Equipment
        | Inventory
        | OperationsLog
        | CashFlow
        | BudgetVsActual

    /// Report metadata
    type ReportMetadata = {
        Title: string
        GeneratedDate: DateTime
        DateRangeStart: DateTime option
        DateRangeEnd: DateTime option
        GeneratedBy: string
        Format: ReportFormat
    }

    /// Generate report header
    let generateHeader (metadata: ReportMetadata) : string =
        let dateRange =
            match metadata.DateRangeStart, metadata.DateRangeEnd with
            | Some s, Some e -> sprintf " (%s to %s)" (s.ToString("MM/dd/yyyy")) (e.ToString("MM/dd/yyyy"))
            | _ -> ""

        sprintf """
================================================================================
%s%s
================================================================================
Generated: %s
By: %s
Format: %A
================================================================================
""" metadata.Title dateRange (metadata.GeneratedDate.ToString("MM/dd/yyyy HH:mm")) metadata.GeneratedBy metadata.Format

    /// Field performance summary row
    type FieldPerformanceRow = {
        FieldName: string
        Acreage: float
        Crop: string
        YieldPerAcre: float
        RevenuePerAcre: decimal
        CostPerAcre: decimal
        ProfitPerAcre: decimal
        ROI: float
    }

    /// Generate field performance table
    let generateFieldPerformanceTable (rows: FieldPerformanceRow list) : string =
        let header = "| Field | Acres | Crop | Yield/Ac | Rev/Ac | Cost/Ac | Profit/Ac | ROI |"
        let separator = "|-------|-------|------|----------|--------|---------|-----------|-----|"

        let dataRows =
            rows
            |> List.map (fun r ->
                sprintf "| %s | %.1f | %s | %.1f | $%.2f | $%.2f | $%.2f | %.1f%% |"
                    r.FieldName r.Acreage r.Crop r.YieldPerAcre r.RevenuePerAcre r.CostPerAcre r.ProfitPerAcre r.ROI)
            |> String.concat "\n"

        sprintf "%s\n%s\n%s" header separator dataRows

// =============================================================================
// GRAIN MARKETING
// =============================================================================

module GrainMarketing =

    /// Basis calculation
    type BasisRecord = {
        Date: DateTime
        Location: string
        CashPrice: decimal
        FuturesPrice: decimal
        Basis: decimal
    }

    /// Calculate basis
    let calculateBasis (cashPrice: decimal) (futuresPrice: decimal) : decimal =
        cashPrice - futuresPrice

    /// Marketing contract types
    type ContractType =
        | CashSale
        | ForwardContract
        | BasisContract
        | HedgeToArrive
        | MinimumPrice
        | AccumulatorContract

    /// Marketing position
    type MarketingPosition = {
        ContractType: ContractType
        Bushels: float
        Price: decimal
        DeliveryStart: DateTime
        DeliveryEnd: DateTime
        Location: string
        ContractNumber: string
    }

    /// Calculate unpriced bushels
    let calculateUnpricedBushels (expectedProduction: float) (positions: MarketingPosition list) : float =
        let pricedBushels = positions |> List.sumBy (fun p -> p.Bushels)
        expectedProduction - pricedBushels

    /// Calculate weighted average price
    let weightedAveragePrice (positions: MarketingPosition list) : decimal =
        let totalBushels = positions |> List.sumBy (fun p -> p.Bushels)
        if totalBushels > 0.0 then
            let totalValue = positions |> List.sumBy (fun p -> p.Price * decimal p.Bushels)
            totalValue / decimal totalBushels
        else
            0m

    /// Storage decision analysis
    type StorageDecision = {
        SellNowPrice: decimal
        ExpectedFuturePrice: decimal
        MonthsToStore: int
        StorageCostPerBuPerMonth: decimal
        InterestRate: float
        Recommendation: string
    }

    /// Analyze store vs sell decision
    let analyzeStorageDecision
        (currentPrice: decimal)
        (expectedPrice: decimal)
        (months: int)
        (storageCost: decimal)
        (interestRate: float)
        (bushels: float) : StorageDecision =

        let totalStorageCost = storageCost * decimal months
        let interestCost = currentPrice * decimal interestRate * decimal months / 12.0m
        let totalCarryCost = totalStorageCost + interestCost
        let netExpectedPrice = expectedPrice - totalCarryCost

        let recommendation =
            if netExpectedPrice > currentPrice then
                sprintf "STORE - Expected gain of $%.2f/bu" (netExpectedPrice - currentPrice)
            else
                sprintf "SELL NOW - Storage would cost $%.2f/bu more than potential gain" (totalCarryCost - (expectedPrice - currentPrice))

        {
            SellNowPrice = currentPrice
            ExpectedFuturePrice = expectedPrice
            MonthsToStore = months
            StorageCostPerBuPerMonth = storageCost
            InterestRate = interestRate
            Recommendation = recommendation
        }

// =============================================================================
// LIVESTOCK INTEGRATION
// =============================================================================

module Livestock =

    /// Animal species
    type Species =
        | Cattle
        | Hog
        | Poultry
        | Sheep
        | Goat
        | Horse

    /// Animal record
    type Animal = {
        Id: Guid
        TagNumber: string
        Species: Species
        Breed: string
        BirthDate: DateTime option
        Sex: string
        Status: string
        CurrentWeight: float option
        Location: string
    }

    /// Weight gain record
    type WeightRecord = {
        AnimalId: Guid
        Date: DateTime
        Weight: float
        Notes: string option
    }

    /// Calculate Average Daily Gain (ADG)
    let calculateADG (weights: WeightRecord list) : float option =
        match weights |> List.sortBy (fun w -> w.Date) with
        | [] | [_] -> None
        | sorted ->
            let first = sorted |> List.head
            let last = sorted |> List.last
            let days = (last.Date - first.Date).TotalDays
            if days > 0.0 then
                Some ((last.Weight - first.Weight) / days)
            else
                None

    /// Feed conversion ratio
    let calculateFeedConversion (feedConsumed: float) (weightGain: float) : float option =
        if weightGain > 0.0 then Some (feedConsumed / weightGain)
        else None

    /// Breeding record
    type BreedingRecord = {
        DamId: Guid
        SireId: Guid option
        BreedingDate: DateTime
        ExpectedDueDate: DateTime
        ActualBirthDate: DateTime option
        NumberBorn: int option
        Notes: string option
    }

    /// Calculate expected due date
    let calculateDueDate (species: Species) (breedingDate: DateTime) : DateTime =
        let gestationDays =
            match species with
            | Cattle -> 283
            | Hog -> 114
            | Sheep -> 147
            | Goat -> 150
            | Horse -> 340
            | Poultry -> 21  // Incubation for chickens
        breedingDate.AddDays(float gestationDays)

// =============================================================================
// DEMO / ENTRY POINT
// =============================================================================

printfn "AgTools Domain Models and Analytics"
printfn "===================================="
printfn ""
printfn "Modules loaded:"
printfn "  - Calculations (GDD, spray conditions, financials)"
printfn "  - FertilizerOptimization (nutrient costs, nitrogen rates)"
printfn "  - YieldResponse (EOR, response curves, profitability)"
printfn "  - Sustainability (carbon footprint, scores, grades)"
printfn "  - Reports (field performance, cost analysis)"
printfn "  - GrainMarketing (basis, contracts, storage decisions)"
printfn "  - Livestock (animals, weights, breeding)"
printfn ""

// Demo calculations
printfn "Demo: GDD Calculation"
printfn "---------------------"
let gdd = Calculations.calculateGDD 85.0 60.0 50.0
printfn "High: 85°F, Low: 60°F, Base: 50°F → GDD: %.1f" gdd

let stage = Calculations.predictCornStage 1200.0
printfn "At 1200 accumulated GDD, corn is at: %A" stage

printfn ""
printfn "Demo: Spray Conditions"
printfn "----------------------"
let weather = {
    Temperature = 72.0
    WindSpeed = 7.0
    WindDirection = "SW"
    Humidity = 55.0
    DewPoint = 52.0
    ChanceOfRain = 10.0
    InversionRisk = false
}
let sprayRating = Calculations.evaluateSprayConditions weather
printfn "Current conditions rated: %A" sprayRating

printfn ""
printfn "Demo: Break-Even Analysis"
printfn "-------------------------"
let breakEvenYield = Calculations.calculateBreakEvenYield 850m 5.50m
let breakEvenPrice = Calculations.calculateBreakEvenPrice 850m 180.0
printfn "Total costs: $850/acre, Corn price: $5.50/bu"
printfn "Break-even yield: %.1f bu/acre" breakEvenYield
printfn "Break-even price (at 180 bu/ac): $%.2f/bu" breakEvenPrice

printfn ""
printfn "Demo: Economic Optimum Rate"
printfn "---------------------------"
let (a, b, c) = YieldResponse.defaultCornNitrogenParams
let eor = YieldResponse.calculateEOR b c 0.50 5.50
let maxRate = YieldResponse.calculateMaxYieldRate b c
printfn "N price: $0.50/lb, Corn: $5.50/bu"
printfn "Economic Optimum Rate: %.0f lbs N/acre" eor
printfn "Max Yield Rate: %.0f lbs N/acre" maxRate
printfn "Savings by using EOR: %.0f lbs N/acre" (maxRate - eor)

printfn ""
printfn "Demo: Sustainability Score"
printfn "--------------------------"
let susScore = Sustainability.calculateSustainabilityScore 350.0 15.0 25.0 75.0
let grade = Sustainability.gradeFromScore susScore
printfn "Carbon: 350 kg/ac, Water: 15 gal/bu, Pesticide reduction: 25%%, Soil health: 75"
printfn "Sustainability Score: %.1f (%s)" susScore grade

printfn ""
printfn "Domain modeling complete. Ready for integration with AgTools backend."
